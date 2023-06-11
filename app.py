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


from absl import flags

flags.DEFINE_string('file_name', None, 'Name of the file where data will be stored')

load_dotenv()

# create the extension
db = SQLAlchemy()

app = Flask(__name__)

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
	time = db.Column(db.DateTime, nullable=True)


@app.before_first_request
def parse_flags():
	flags.FLAGS(sys.argv)

	# Configure the SQLite database, relative to the app instance folder
	# TODO(toni) Make this more clean.
	# If local it will use the DATABASE_URL stored in the local .env.
	# If running on heroku it will use url of Postgres.
	database_url = os.getenv("DATABASE_URL")
	if database_url.startswith('postgres://'):
		database_url = database_url.replace(
			'postgres://', 'postgresql://', 1)
	logging.info(database_url)
	app.config["SQLALCHEMY_DATABASE_URI"] = database_url

	# Initialize the app with the extension
	db.init_app(app)

	# Create the database.
	with app.app_context():
		db.create_all()


@app.route('/')
def hello():
	return 'Hello, World!'


# The feeling prompt: Expected output is of the form:
# < NEG | POS | NEURTRAL >
# <question> Why do you feel x </question>.
_FEELING_PROMPT = """For the following feelings please identify is the sentiment is positive (POS), negative (NEG) or neutral (NEUTRAL). Then referring to the feeling ask what happened to make them feel this way. The question should be asked in a friendly manner. If the sentence already describes the event, ask for a little more information about it.

Here are some examples:

Feeling: I'm good, thanks.
POS
<question> That's good to hear. What's going well for you today? </question>

Feeling: Feeling a bit sad today.
NEG
<question> Sorry to hear this. What's happened to make you feel sad? </question>

Feeling: I've got a big presentation coming up and I'm super anxious!
NEG
<question> Oh, no! Tell me more about the presentation? </question>

Feeling: {feeling}
"""

def feelings_post_process(model_output: str) -> str:
	"""Post processes outputs from the _FEELING_PROMPT prompt."""

	# Get the sentiment.
	sentiment = None
	if 'POS' in model_output:
		sentiment = Sentiment.POS.value
	elif 'NEG' in model_output:
		sentiment = Sentiment.NEG.value
	elif 'NEUTRAL' in model_output:
		sentiment = Sentiment.NEUTRAL.value
	else:
		logging.warning('Sentiment in %s not detected!', model_output)

	# Get the question
	question = utils.post_process_tags(model_output, 'question')

	return dict(
		sentiment=sentiment, question=question)


@app.post('/feeling_test')
def user_feeling_test():
	"""TEST Response to: How are you feeling today?"""
	# Prepare the response.
	# TODO(toni) Format feelings into a feelings string.
	response = {
		'sentiment': Sentiment.NEG.value, 
		'question': 'What\'s got you feeling sad?',
	}

	# Return a JSON response
	return jsonify(response)

@app.post('/feeling')
@validate_twilio_request
def user_feeling():
	"""Response to: How are you feeling today?"""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	logging.info("message_body:", message_body)

	# Create the sentiment prompt.
	# The "feeling" key comes from the http_feeling widget on the Twilio side.
	sentiment_prompt = _FEELING_PROMPT.format(
		feeling=message_body['feeling'])

	# Call to the LLM
	model_output = call_api(
		origin='user_feeling',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=sentiment_prompt)

	# Post-process the output to get the sentiment and feelings.
	response = feelings_post_process(model_output)

	# Return a JSON response
	return jsonify(response)


# The ask for thought prompt: Expected output is:
# <question> question </question>.
# Asking the the user for any self-talk/beliefs/thoughts in the
# context of the event. 
# This prompt includes one example.
_ASKING_FOR_THOUGHT_PROMPT = """The following sentence is an activating event identified during the ABC of a CBT session. "{event}" You must now ask the user to identify any thoughts, beliefs or self-talk to help keep them on track with their CBT session. Give your response must start with <question> followed by the question to identify self-talk, beliefs or thoughts. End with </question>. Ask the question in a friendly way.
"""

_DEFAULT_ASK_FOR_THOUGHT = """
When you think about this situation, what's going through your head? Any recurring thoughts or beliefs?"""

def ask_for_thought_post_processing(model_output: str) -> str:
	"""Post processes outputs from the _ASKING_FOR_THOUGHT prompt."""

	question = utils.post_process_tags(model_output, 'question')

	return dict(question=question)

@app.post('/thought')
@validate_twilio_request
def ask_for_thought():
	"""Asks user for their thoughts, belief or self-talk."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Create the feelings prompt.
	# The "event" key comes from the http_ask_for_thought widget on the Twilio side.
	prompt = _ASKING_FOR_THOUGHT_PROMPT.format(
		event=message_body['event'])

	# Call to the LLM
	model_output = call_api(
		origin='ask_for_thought',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# Post process the response to get the distortion and question to ask the user.
	response = ask_for_thought_post_processing(model_output)

	return jsonify(response)


_DISTORTION_DETECTION_PROMPT = """
For the following sentence you need to identify the distortions in the users thinking and pose a question to help them realise that distortion. For distortion question pair you must start on a new line with the key <distortion> followed by the distortion, end this with </distortion>. Then on the next line write <question> followed by a question that would help someone identify the distortion, end this with </question>. The question should not directly reference the distortion and should be relevant to the original sentence. "{belief}"
"""

def distortion_detection_post_processing(model_output: str) -> str:
	"""Post processes outputs from the _DISTORTION_DETECTION_PROMPT prompt."""

	distortion = utils.post_process_tags(model_output, 'distortion')
	question = utils.post_process_tags(model_output, 'question')

	if not question.endswith('?'):
		logging.warning('The question, %s, does not end with a "?".')

	return dict(distortion=distortion, question=question)

@app.post('/distortions_test')
def detect_distortions_test():
	"""TEST Detect distortions in the users belief."""
	# Prepare the response.
	response = {
		'distortion': 'Personalization', 
		'question': 'Are there any external factors or circumstances that contributed to the outcome, or are you solely responsible for the perceived failure?',
	}

	# Return a JSON response
	return jsonify(response)

@app.post('/distortions')
@validate_twilio_request
def detect_distortions():
	"""Detect distortions in the users belief."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Create the feelings prompt.
	# The "belief" key comes from the http_detect_distortions widget on the Twilio side.
	prompt = _DISTORTION_DETECTION_PROMPT.format(
		belief=message_body['belief'])

	# Call to the LLM
	model_output = call_api(
		origin='detect_distortions',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# The model may have recognised several distortions (separated by '\n\n').
	# For now just take one of these.
	# TODO(toni) Use all of the distortions.
	model_output = model_output.split('\n\n')[0]

	# Post process the response to get the distortion and question to ask the user.
	response = distortion_detection_post_processing(model_output)

	return jsonify(response)

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
	# TODO(toni) Call the LLM
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

		flow_datum = FlowDatum(**message_body)
		db.session.add(flow_datum)
		db.session.commit()

		return jsonify({'message': f'Data saved to {file_name}'})
	except Exception as e:
		return jsonify({'error': str(e)})


if __name__ == "__main__":
	app.run(debug=True, use_debugger=True, port=8000)