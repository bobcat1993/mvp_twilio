"""The Flask App to act as an API for our Twilio app. 

These functions can be used later too in the final product.

TODOs:
- Add data logging based on people's numbers.
- Deal with multiple distortions.
- Share the distortion name with the user.
"""
from flask import Flask, jsonify, request
from abc_types import Sentiment
import json
import logging
from utils import call_api as call_api
import utils
import copy
import os
import sys
import datetime
from hashlib import md5
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from utils import validate_twilio_request
import openai
import ast


from absl import flags

flags.DEFINE_string('file_name', None, 'Name of the file where data will be stored')

load_dotenv()

# create the extension
db = SQLAlchemy()

app = Flask(__name__)

# See all the logs.
# app.logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

OUT_GPT_DATA_PATH = 'data/gpt_outputs'
# OUT_FLOW_DATA_PATH = 'data/flow_outputs'


class FlowDatum(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	user_feeling = db.Column(db.String, nullable=True)
	user_event = db.Column(db.String, nullable=True)
	bot_feeling = db.Column(db.String, nullable=True)
	user_belief = db.Column(db.String, nullable=True)
	bot_distortions = db.Column(db.String, nullable=True)
	user_rephrase = db.Column(db.String, nullable=True)
	user_feel_after = db.Column(db.String, nullable=True)
	user_feedback = db.Column(db.String, nullable=True)
	flow_sid = db.Column(db.String, nullable=True)
	origin = db.Column(db.String, nullable=True)
	user_id = db.Column(db.String, nullable=True)
	error = db.Column(db.String, nullable=True)
	event_history = db.Column(db.String, nullable=True)
	distortion_history = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)


@app.before_first_request
def init_app():
	flags.FLAGS(sys.argv)

	# Configure the SQLite database, relative to the app instance folder
	# TODO(toni) Make this more clean.
	# If local it will use the DATABASE_URL stored in the local .env.
	# If running on heroku it will use url of Postgres.
	database_url = os.getenv("DATABASE_URL")
	if database_url.startswith('postgres://'):
		database_url = database_url.replace(
			'postgres://', 'postgresql://', 1)
	app.logger.info(database_url)
	app.config["SQLALCHEMY_DATABASE_URI"] = database_url

	# Initialize the app with the extension
	db.init_app(app)

	# Create the database.
	with app.app_context():
		db.create_all()

	# Setup the openai API.
	utils.setup_openai()


@app.route('/')
def hello():
	return 'Hello, World!'


_DEFAULT_ASK_FOR_FEELING = """Tell me more about what\'s happened to make you feel this way?"""

# The detect sentiment prompt: Expected output is of the form:
# < NEG | POS | NEURTRAL >
_SENTIMENT_SYSTEM_PROMPT = """The user will specify how they are feeling. You must identify the sentiment as positive (POS), negative (NEG) or neutral (NEUTRAL).

Respond with one of POS, NEG or NEUTRAL.

If someone says they are good, this should be considered positive."""

def detect_sentiment_post_process(model_output: str):
	# Get the sentiment.
	sentiment = None
	if 'POS' in model_output:
		sentiment = Sentiment.POS.value
	elif 'NEG' in model_output:
		sentiment = Sentiment.NEG.value
	elif 'NEUTRAL' in model_output:
		sentiment = Sentiment.NEUTRAL.value
	# As a last resort test the lower cases.
	elif 'neutral' in model_output:
		app.logger.warning('Assuming NEUTRAL in %s', model_output)
		sentiment = Sentiment.NEUTRAL.value
	elif 'neg' in model_output:
		app.logger.warning('Assuming NEG in %s', model_output)
		sentiment = Sentiment.NEG.value
	elif 'pos' in model_output:
		app.logger.warning('Assuming POS in %s', model_output)
		sentiment = Sentiment.POS.value
	else:
		app.logger.warning('Sentiment in %s not detected!', model_output)

	return dict(sentiment=sentiment)

@app.post('/detect_sentiment')
def detect_sentiment():

	# Retrieve data from the request sent by Twilio
	message_body = request.json
	user_feeling = message_body['feeling']

	# TODO(toni) Consider including "How are you feeling..." text too.
	messages= [
		{"role": "system", "content": _SENTIMENT_SYSTEM_PROMPT},
		{"role": "user", "content": user_feeling}
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	model_output = model_output['choices'][0]['message']['content']

	# Post-process the output to get the sentiment and feelings.
	response = detect_sentiment_post_process(model_output)

	# Return a JSON response
	return jsonify(response)

_ASK_FOR_EVENT_SYSETM_PROMPT = """You are a focused, friendly assistant and you have one goal. The user has told how they are feeling, find out what event has made them feel this way. 

For example, if the user say that are good, ask why they are feeling good and if the user says they are sad, find our what happened to make them sad.

When you know the event, respond with "STOP EVENT DETECTED" followed by a short sentence summarising the event."""

# TODO(toni) If after a fixed number of step no event is detected do something.
# We can compute steps by the len(history).
@app.post('/ask_for_event')
@validate_twilio_request
def ask_for_event():
	"""Detects if the user has specified an event.
	
	Checks if the current user_event contains a user event. If it does
		this information is returned. If not the model continues to ask
		questions and update the history until an event has been detected.

	"""
	message_body = request.json

	user_feeling = message_body['user_feeling']
	history = message_body['event_history']

	current_user_event = message_body['last_user_response']

	# Hacky way to add the previous user response, since
	if current_user_event:
		history.append({"role": "user", "content": current_user_event})

	app.logger.info('[ask_for_event] history: %s', history)

	messages= [
		{"role": "system", "content": _ASK_FOR_EVENT_SYSETM_PROMPT},
		{"role": "assistant", "content": "How are you feeling right now?"},
		{"role": "user", "content": user_feeling},
		*history,
	]

	# Using the chat_completion that's wrapped in a retry.
	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	next_question = model_output['choices'][0]['message']['content']
	history.append({"role": "assistant", "content": next_question})

	# Check if there is an event detected.
	has_event = True if 'STOP EVENT DETECTED' in next_question else False

	if has_event:
		# Don't use the raw value from the user any more.
		# user_event = current_user_event
		user_event = next_question.split('DETECTED')[-1].strip()

		if not user_event:
			user_event = current_user_event
	
	return jsonify(
		has_event=has_event,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		user_event=current_user_event)


# The ask for thought prompt: Expected output is:
# <question> question </question>.
# Asking the the user for any self-talk/beliefs/thoughts in the
# context of the event. 
# This prompt includes one example.
_ASK_FOR_THOUGHT_SYSTEM_PROMPT = """The assistant has provided a summary the users event. Ask the user a short question to help them identify any thoughts, beliefs or self-talk. Do not ask a yes/no question."""

_DEFAULT_ASK_FOR_THOUGHT = """
When you think about this situation, what's going through your head? Any recurring thoughts or beliefs?"""

@app.post('/thought')
@validate_twilio_request
def ask_for_thought():
	"""Asks user for their thoughts, belief or self-talk."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json
	user_event = message_body['event']

	# Generate a question to ask the user for their thoughts about an event.
	# TODO(toni) Consider including the user event.
	messages= [
		{"role": "system", "content": _ASK_FOR_THOUGHT_SYSTEM_PROMPT},
		{"role": "user", "content": user_event},
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	question = model_output['choices'][0]['message']['content']

	response = dict(question=question)

	return jsonify(response)

_DISTORTION_SYSTEM_PROMPT = """
The user has shared a belief with you. You must now identify a distortion in their thinking and ask them short questions to help them realise that distortion. This should be framed in a friendly way and take the side of the user.

The conversation must finish after no more than three turns. Respond with "DONE" when the user has identified the distortion and say something appropriate to end the conversation on this turn. Do not include any questions on this turn."""

MAX_STEPS = 6  # Relates to the "three" above.

@app.post('/distortion_loop')
@validate_twilio_request
def distortion_loop():
	"""Asks the users question to help identify distortions.
	
	Asks the user questions until the conversation in DONE.

	"""
	message_body = request.json

	user_belief = message_body['user_belief']
	history = message_body['distortion_history']

	current_user_response = message_body['last_user_response']

	# Add the previous user response to the end of the history.
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	app.logger.info('[distortion_loop] history: %s', history)

	messages= [
		{"role": "system", "content": _DISTORTION_SYSTEM_PROMPT},
		{"role": "user", "content": user_belief},
		*history,
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	next_question = model_output['choices'][0]['message']['content']
	history.append({"role": "assistant", "content": next_question})

	# Check if there is an event detected.
	is_done = True if 'DONE' in next_question else False

	if len(messages) == MAX_STEPS:
		app.logger.warn('is_done != True, but has reached 6 messages.')
		is_done = True

	if is_done:
		next_question = next_question.replace('DONE', '')
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
	)


_POSITIVE_FEEDBACK_PROMPT = """
For the following sentence, start your response with <response> then write down a sentence, in the 2nd person, praises the user if they have achieve something, otherwise response appropriately in a supportive way. End with </response >. Do not ask any questions. "{positive_event}"
"""

def positive_feedback_post_processing(model_output: str) -> str:
	"""Post processes outputs from the _DISTORTION_DETECTION_PROMPT prompt."""

	response = utils.post_process_tags(model_output, 'response')

	return dict(response=response)

@app.post('/positive_feedback_test')
def positive_feedback_test():
	"""TEST: Responds to users reason for being in a positive mood."""
	response = {
		'response': 'Great work today!',
	}
	# Return a JSON response
	return jsonify(response)


@app.post('/positive_feedback')
@validate_twilio_request
def positive_feedback():
	"""Responds to users reason for being in a positive mood."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Create the feelings prompt.
	# The "belief" key comes from the http_detect_distortions widget on the Twilio side.
	prompt = _POSITIVE_FEEDBACK_PROMPT.format(
		positive_event=message_body['positive_user_event'])

	# Call to the LLM
	model_output = call_api(
		origin='positive_feedback',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# Post process the response to get the distortion and question to ask the user.
	response = positive_feedback_post_processing(model_output)

	return jsonify(response)

def string_hash(string):
	return md5(string.encode()).hexdigest()

@app.post('/save_abc_data')
@validate_twilio_request
def save_abc_data():
	"""Saves data at the end of the ABC chat."""
	# Retrieve data from the request sent by Twilio
	file_name = flags.FLAGS.file_name
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		now = datetime.datetime.now()
		message_body['time'] = now

		# Dump the event and distortion history (into dicts).
		message_body['event_history'] = json.dumps(message_body['event_history'])
		message_body['distortion_history'] = json.dumps(message_body['distortion_history'])

		# Dump other bot responses.
		message_body['bot_feeling'] = json.dumps(message_body['bot_feeling'])
		message_body['bot_distortions'] = json.dumps(message_body['bot_distortions'])

		flow_datum = FlowDatum(**message_body)
		db.session.add(flow_datum)
		db.session.commit()

		return jsonify({'message': f'Data saved to {file_name}'})
	except Exception as e:
		return jsonify({'error': str(e)})


if __name__ == "__main__":
	app.run(debug=True, use_debugger=True, port=8000)