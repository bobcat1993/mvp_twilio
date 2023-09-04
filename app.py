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
import requests
import pygal

import create_post

# Import features.
from features import sphere_of_influence
from features import reminders
from features import challenge

# Import journeys
from journeys import boundaries


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
	"""Stores the data from the Reflect flow."""

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


class CheerFlowDatum(db.Model):
	"""Stores the data from the Cheerleader flow."""

	id = db.Column(db.Integer, primary_key=True)
	user_event = db.Column(db.String, nullable=True)
	http_ask_for_person = db.Column(db.String, nullable=True)
	user_identifies_person = db.Column(db.String, nullable=True)
	history = db.Column(db.String, nullable=True)
	last_bot_cheer = db.Column(db.String, nullable=True)
	user_feel_after = db.Column(db.String, nullable=True)
	flow_sid = db.Column(db.String, nullable=True)
	origin = db.Column(db.String, nullable=True)
	user_id = db.Column(db.String, nullable=True)
	error = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)


class GoalFlowDatum(db.Model):
	"""Stores the data from the SMART goal setting flow."""

	id = db.Column(db.Integer, primary_key=True)
	user_goal = db.Column(db.String, nullable=True)
	history = db.Column(db.String, nullable=True)
	user_feel_after = db.Column(db.String, nullable=True)
	flow_sid = db.Column(db.String, nullable=True)
	origin = db.Column(db.String, nullable=True)
	user_id = db.Column(db.String, nullable=True)
	error = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)


class ControlFlowDatum(db.Model):
	"""Stores the data from the SMART goal setting flow."""

	id = db.Column(db.Integer, primary_key=True)
	user_event = db.Column(db.String, nullable=True)
	history = db.Column(db.String, nullable=True)
	user_feel_after = db.Column(db.String, nullable=True)
	flow_sid = db.Column(db.String, nullable=True)
	origin = db.Column(db.String, nullable=True)
	user_id = db.Column(db.String, nullable=True)
	error = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)


class UserDatum(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	user_number = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)
	flow_name = db.Column(db.String, nullable=True)


class ProfileDatum(db.Model):
	"""A user profile."""

	id = db.Column(db.Integer, primary_key=True)
	user_number = db.Column(db.String, nullable=True)
	user_email = db.Column(db.String, nullable=True)
	expiry_date = db.Column(db.Integer, nullable=True)
	user_wix_id = db.Column(db.String, nullable=True)


class UserFeedbackDatum(db.Model):
	"""A user feedback at the end of a chat."""

	id = db.Column(db.Integer, primary_key=True)
	time = db.Column(db.DateTime, nullable=True)
	flow_name = db.Column(db.String, nullable=True)
	user_feedback = db.Column(db.String, nullable=True)


class ReminderDatum(db.Model):
	"""A reminders sent via WhatsApp"""

	id = db.Column(db.Integer, primary_key=True)
	user_number = db.Column(db.String, nullable=True)
	message = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)
	
# Datum for the journeys.
BoundariesStageOneDatum = boundaries.get_BoundariesStageOneDatum(db)

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


@app.post('/user_feeling')
def user_feeling():
	"""Asks the user how they are feeling based on the time of day."""

	early = datetime.time(00, 00, 00)
	morning = datetime.time(6, 00, 00)
	afternoon = datetime.time(12, 00, 00)
	evening = datetime.time(17, 00, 00)
	late = datetime.time(23, 00, 00)

	# Get the current time.
	time = datetime.datetime.now().time()
	
	if (time > late):
		response = "I notice you are up late. How are you feeling?"

	elif (time > early) & (time < morning):
		response = "It seems early. How are you feeling?"

	elif (time > morning) & (time < afternoon):
		response = "Let's start. How you are feeling this morning?"

	elif (time > afternoon) & (time < evening):
		response = "Let's begin. How are you feeling this afternoon?"

	elif (time > evening) & (time < late):
		response = "Let's start. How have you been feeling this evening?"
	else:
		response = "Let's begin. How are you feeling?"

	return jsonify(response=response)

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

	return sentiment

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
	sentiment = detect_sentiment_post_process(model_output)

	# Return a JSON response
	return jsonify(sentiment=sentiment)

_ASK_FOR_EVENT_SYSETM_PROMPT = """In this coaching session, the friendly assistant wants to understand what has caused a user to feel a certain way.

The assistant must ask short, friendly questions to find out what event has occurred to make the user feel the way they do.

At the end the assistant must respond "STOP EVENT DETECTED"  and give a one sentence summary of the event. The assistant must not ask any additional questions and should keep the total interaction as short as possible."""

# TODO(toni) If after a fixed number of step no event is detected do something better than just ending the conversation.
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

	# Hacky way to add the previous user response.
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
		user_event = user_event.strip('.,:- ')

		if not user_event:
			user_event = None
	else:
		user_event = None

	# Stop if there is no question in next_question.
	if '?' not in next_question:
		# TODO(toni) This will result in an empty event. Need to compute a user event.
		has_event = True
	
	return jsonify(
		has_event=has_event,
		messages=messages,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		user_event=user_event)


# The ask for thought prompt:
_ASK_FOR_THOUGHT_SYSTEM_PROMPT = """The assistant has provided the a summary of an event that the user experienced.

Now the assistant must ask the user a short question to help them identify any thoughts, beliefs or self-talk. The assistant must not ask a question whose answer is yes or no."""

_DEFAULT_ASK_FOR_THOUGHT = """
When you think about this situation, what's going through your head? Any recurring thoughts or beliefs?"""

# TODO(toni) Deprecate this one.
@app.post('/thought')
@validate_twilio_request
def ask_for_thought():
	"""Asks user for their thoughts, belief or self-talk."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json
	user_event = message_body['event']

	# If there was no user event detected, ask the default question.
	if not user_event:
		return dict(question=_DEFAULT_ASK_FOR_THOUGHT)

	# Generate a question to ask the user for their thoughts about an event.
	# TODO(toni) Consider including the user event history.
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

	return jsonify(question=question)


_REFLECT_ASSISANT_ASK_FOR_EVENT = """To being, I'd love for you to share with me a particular event, challenge or situation that's been playing on your mind recently."""

# The ask for thought prompt:
_ASK_FOR_THOUGHT_SYSTEM_PROMPT_V2 = """In this coaching session, the assistant is helping the user identify and challenge unhelpful thoughts.

Referring to the event specified by the user,
explain to the user that you are going to help them reflect on this event. To start, ask them share any thoughts, self-talk or beliefs that arise from the event.

This should be contained in a single, friendly and brief response that ends with a question."""

# TODO(toni) Deprecate this one.
@app.post('/reflect/ask_for_belief_loop')
@validate_twilio_request
def ask_for_belief_loop():
	"""Asks user for their thoughts, belief or self-talk."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json
	user_event = message_body['user_event']
	history = message_body['history']
	last_user_response = message_body['last_user_response']

	if last_user_response:
		history.append({"role": "user", "content": last_user_response})

	# Generate a question to ask the user for their thoughts about an event.
	messages= [
		{"role": "system", "content": _ASK_FOR_THOUGHT_SYSTEM_PROMPT_V2},
		{"role": "assistant", "content": _REFLECT_ASSISANT_ASK_FOR_EVENT},
		{"role": "user", "content": user_event},
		*history
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	question = model_output['choices'][0]['message']['content']
	history.append({"role": "assistant", "content": question})

	def _check_if_asked_for_belief(question):
		"""Check if Bobby has asked about belief."""
		if 'thought' in question:
			return True
		if 'belief' in question:
			return True
		if ('self-talk' in question) or ('self talk' in question):
			return True
		return False

	is_done = _check_if_asked_for_belief(question)

	# Note that the last output from this loop is a question from the 
	# model, not a user response.
	return jsonify(
		question=question,
		messages=messages,
		history=json.dumps(history),
		is_done=is_done)


_DISTORTION_SYSTEM_PROMPT = """
The user has shared a belief with you. You must now identify a distortion in their thinking (no need to share it with them) and ask them short questions to help them realise that distortion. This should be framed in a friendly way and take the side of the user.

The conversation must finish after no more than six turns. Respond with "SESSION FINISHED" when the user has identified the distortion and say something appropriate to end the conversation on this turn. Do not include any questions on this turn.
"""

@app.post('/reflect/distortion_loop')
@validate_twilio_request
def distortion_loop():
	"""Asks the users question to help identify distortions.
	
	Asks the user questions until the conversation in DONE.

	"""
	message_body = request.json

	user_event = message_body['user_event']
	# belief_history does not include final user response.
	belief_history = message_body['belief_history']
	# user_belief is the final user response.
	user_belief = message_body['user_belief']
	history = message_body['distortion_history']

	# Append the user response to the belief history.
	belief_history.append({"role": "user", "content": user_belief})

	# Add the previous user response to the end of the history.
	current_user_response = message_body['last_user_response']
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	app.logger.info('[distortion_loop] history: %s', history)

	print("belief_history:", belief_history)
	print("history:", history)

	messages= [
		{"role": "system", "content": _DISTORTION_SYSTEM_PROMPT},
		{"role": "assistant", "content": _REFLECT_ASSISANT_ASK_FOR_EVENT},
		{"role": "user", "content": user_event},
		*belief_history,
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
	is_done = True if 'SESSION FINISHED' in next_question else False

	# If there is no question, then consider the loop done.
	if '?' not in next_question:
		is_done = True

	if is_done:
		next_question = next_question.replace('SESSION FINISHED', '')
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
	)


_POSITIVE_FEEDBACK_SYSTEM_PROMPT = """
The assistant has provided a summary of a users event.

You must praises the user if they have achieve something, otherwise response appropriately in a supportive way. 

Do not ask any question and do not refer to the user; the response must be in the second person."""

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

	positive_event = message_body['positive_user_event']

	messages= [
		{"role": "system", "content": _POSITIVE_FEEDBACK_SYSTEM_PROMPT},
		{"role": "assistant", "content": positive_event},
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	response = model_output['choices'][0]['message']['content']

	return jsonify(response=response)

# Large-ish number for the max number of steps before the cheer loop is ended.
MAX_CHEER_STEPS = 30

_CHEER_SYSTEM_PROMPT = """
In this coaching session, the assistant is helping the user practice being their own cheerleader.

Referring to the friend chosen by the user, the assistant must tell the user to imagine that the friend they chose is sitting in front of them right now and that what happened to the user today happened to that friend, and they are experiencing the same feelings as the user is right now. Tell the user that they are their friend's cheerleader and ask them what would say to make their friend feel better.

Once the user says something positive, encourage them to add to that. Then get them to say these same words to them self and ask how they feel.

When the session is finished the assistant should say "SESSION FINISHED".

Keep all responses short and friendly.
"""

# The assistant asks the user for an event.
_CHEER_ASSISANT_ASK_FOR_EVENT = """To get started, I'd love to hear about a  particular event, challenge, or situation where you could use some support and encouragement."""

# The assistant asks the user to choose someone to cheer on. 
_CHEER_ASSISTANT_CHOOSE_SOMEONE = """Now, let’s practise showing the same compassion we have for others to ourselves. To start, I want you to think of a friend. They can be anyone, the only condition is that they are someone you care for. Let me know who you choose?"""

@app.post('/cheerleader/cheer_loop')
@validate_twilio_request
def cheer_loop():
	"""Gets the user for cheer a friend and redirect to themselves."""

	# Get the inputs.
	message_body = request.json
	history = message_body['cheer_history']
	user_event = message_body['user_event']
	user_identifies_person = message_body['user_identifies_person']
	current_user_response = message_body['last_user_response']

	# Add the previous user response to the end of the history.
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	messages = [
	{"role": "system", "content": _CHEER_SYSTEM_PROMPT},
	{"role": "assistant", "content": _CHEER_ASSISANT_ASK_FOR_EVENT},
	{"role": "user", "content": user_event},
	{"role": "assistant", "content": _CHEER_ASSISTANT_CHOOSE_SOMEONE},
	{"role": "user", "content": user_identifies_person},
	*history
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
	is_done = True if 'SESSION FINISHED' in next_question else False

	if len(messages) == MAX_CHEER_STEPS:
		app.logger.warn(f'is_done != True, but has reached {MAX_CHEER_STEPS} messages.')
		is_done = True

	if is_done:
		next_question = next_question.replace('SESSION FINISHED', '')
		next_question = next_question.strip(' .\n')

	# If there is no question in "next_question" also set is_done to True.
	if '?' not in next_question:
		is_done = True
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)

_ASK_FOR_PERSON_SYSTEM_PROMPT = """In this coaching session, the assistant is helping the user practice being their own cheerleader.

Referring to the event specified by the user,
explain to the user that you are going to help them practise showing the same compassion and support that have for others to themselves.  To start, ask them to think of a friend. Tell them that they can choose anyone, the only condition is that they are someone the user cares for. Ask they user who they chose.

This should be contained in a single, friendly and brief response that ends with a question.
"""

@app.post('/cheerleader/ask_for_person')
@validate_twilio_request
def ask_for_person():
	"""Asks the user to choose a person after user shares event."""

	# Get the inputs.
	message_body = request.json
	user_event = message_body['user_event']

	messages = [
	{'role': 'system', 'content': _ASK_FOR_PERSON_SYSTEM_PROMPT},
	{'role': 'assistant', 'content': _CHEER_ASSISANT_ASK_FOR_EVENT},
	{'role': 'user', 'content': user_event},
	]

	model_output = utils.chat_completion(
		model='gpt-3.5-turbo-0613',
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	response = model_output['choices'][0]['message']['content']

	return jsonify(response=response)

_MAX_GOAL_STEPS = 30

_GOAL_ASSISANT_ASK_FOR_GOAL = """Let's being, what is your goal for today?"""

_GOAL_SYSTEM_PROMPT = """In this coaching session, the friendly assistant is helping the user set a SMART goal to be completed today.

The assistant should ask the users specific questions, one at a time, to help them refine their initial goal as a SMART goal which is Specific, Measurable, Achievable, Relevant and Time bound.

At the end the assistant should provide a short one sentence summary of the final SMART goal and say SESSION ENDED. Do not let the user set another goal."""


@app.post('/goal/goal_loop')
@validate_twilio_request
def goal_loop():
	"""Helps the user set SMART goals."""

	# Get the inputs.
	message_body = request.json
	history = message_body['goal_history']
	user_goal = message_body['user_goal']
	current_user_response = message_body['last_user_response']

	# Add the previous user response to the end of the history.
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	messages = [
	{"role": "system", "content": _GOAL_SYSTEM_PROMPT},
	{"role": "assistant", "content": _GOAL_ASSISANT_ASK_FOR_GOAL},
	{"role": "user", "content": user_goal},
	*history
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	import pprint
	pprint.pprint(messages)
	next_question = model_output['choices'][0]['message']['content']
	history.append({"role": "assistant", "content": next_question})

	# Check if there is an event detected.
	is_done = True if 'SESSION ENDED' in next_question else False

	if len(messages) == _MAX_GOAL_STEPS:
		app.logger.warn(f'is_done != True, but has reached {MAX_GOAL_STEPS} messages.')
		is_done = True

	if is_done:
		next_question = next_question.replace('SESSION ENDED', '')
		next_question = next_question.strip(' .\n')

	# If there is no question in "next_question" also set is_done to True.
	# N.B. I've not yet seen a case where this does not end correctly.
	if '?' not in next_question:
		is_done = True
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)


def _days_since_start():
	# Replace 'YYYY-MM-DD' with your desired start date in the format 'YYYY-MM-DD'
	start_date_str = '2023-08-07'

	# Convert the start date string to a datetime object
	start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')

	# Get the current date
	current_date = datetime.datetime.today()

	# Compute the difference between the current date and the start date
	days_difference = (current_date - start_date).days

	return days_difference

_GRATITUDE_PROMPTS = [
	"What simple pleasure are you grateful for today, and why?",
	"What’s something that you’re grateful to have today that you didn’t have a year ago?",
	"What top three things/people make your home feel special?",
	"Open your phone or photo album and find a photo that you like. Why are you grateful for this photo? What are you grateful for in the photo?",
	"What’s something or someone that makes you feel safe?",
	"How are you able to help others and how does that make you grateful?",
	"What mistake or failure are you grateful for?",
	"What skill(s) do you have that you’re grateful for?",
	"Which decisions you made in the past are you grateful for today?",
	"Write down an action to do this week, that your future self will be grateful for.",
	"Which childhood memories are you grateful for?",
	"Which personality trait of yours are you are most thankful for?",
	"What is something or someone that you take for granted. How can you express more appreciation for this thing or person?",
	"What has been the highlight of your day today?",
	"Name something that always put a smile on your face."
]

@app.post('/gratitude_challenge/get_gratitude_prompt')
@validate_twilio_request
def get_gratitude_prompt():
	"""Give the gratitude prompt of the day."""

	# Get the day number/ index.
	day_index = _days_since_start()

	# Get the prompt based on the day.
	prompt = _GRATITUDE_PROMPTS[day_index % len(_GRATITUDE_PROMPTS)]
	
	return jsonify(
		day=str(day_index + 1),
		prompt=prompt
	)


_SHARE_GRATITUDE_PROMPTS = [
"Here's a snapshot of your gratitude. Consider sharing it with your friends and colleagues to brighten their day too!",
"Did you know that when your friends and colleagues see what you are grateful for, they get the same positive benefits as you? Consider sharing this snapshot of your gratitude with others.",
"They say, 'Sharing is Caring' even more so when you share what you are grateful for. Consider sharing this snapshot of your gratitude with others.",
"When you share your gratitude with others, it can inspire them to notice and appreciate the good things in their lives too. Consider sharing this snapshot of your gratitude with others.",
"You've just expressed something you're grateful for – now take a moment to share it with a friend. Spread the positivity and let them know what's brightening your day!",
"Share what you're thankful for with a friend and challenge them to pass on their own moments of gratitude. Let's create a ripple of appreciation together.",
"Your gratitude is a gift worth sharing. Consider sharing this snapshot of your gratitude with others."
]

@app.post('/gratitude_challenge/create_post')
@validate_twilio_request
def create_gratitude_post():
	"""Give the gratitude prompt of the day."""

	message_body = request.json
	response = message_body['response']

	# Get the call to action for the user to share their gratitude.
	day_index = _days_since_start()
	share_prompt = _SHARE_GRATITUDE_PROMPTS[day_index % len(_SHARE_GRATITUDE_PROMPTS)]

	# Create the post.
	image_url = create_post.dynapictures_api(response)

	return jsonify(
		image_url=image_url,
		share_prompt=share_prompt)

@app.post('/sphere_of_influence/outside_loop')
@validate_twilio_request
def outside_loop():
	"""Identify what is outside of the users control."""
	return sphere_of_influence.outside_loop(request)

@app.post('/sphere_of_influence/summarise_outside')
@validate_twilio_request
def summarise_outside():
	"""Identify what is outside of the users control."""
	return sphere_of_influence.summarise_outside(request)

@app.post('/sphere_of_influence/inside_loop')
@validate_twilio_request
def inside_loop():
	"""Identify what is inside of the users control."""
	return sphere_of_influence.inside_loop(request)


@app.post('/sphere_of_influence/control_loop')
@validate_twilio_request
def control_loop():
	"""Identify what is outside and inside of the users control."""
	return sphere_of_influence.control_loop(request)


def string_hash(string):
	return md5(string.encode()).hexdigest()

@app.post('/save_user_info')
@validate_twilio_request
def save_user_info():
	"""Saves the users number and time at the start of the chat."""

	message_body = request.json

	# Hash the user_id so that the data is pseudo-anonyms.
	message_body['user_number'] = string_hash(
		message_body['user_number'])

	# Get the current time.
	now = datetime.datetime.now()
	message_body['time'] = now

	user_datum = UserDatum(**message_body)
	db.session.add(user_datum)
	db.session.commit()

	return jsonify({'message': 'User data saved.'})


@app.post('/save_abc_data')
@validate_twilio_request
def save_abc_data():
	"""Saves data at the end of the ABC chat."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
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

		return jsonify({'message': f'Flow data saved.'})
	except Exception as e:
		return jsonify({'error': str(e)})


@app.post('/cheerleader/save_cheer_data')
@validate_twilio_request
def save_cheer_data():
	"""Saves data at the end of the Cheerleader chat."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
		now = datetime.datetime.now()
		message_body['time'] = now

		# Dump the history (into dicts).
		message_body['history'] = json.dumps(message_body['history'])

		flow_datum = CheerFlowDatum(**message_body)
		db.session.add(flow_datum)
		db.session.commit()

		return jsonify({'message': f'Flow data saved.'})
	except Exception as e:
		return jsonify({'error': str(e)})


@app.post('/goal/save_goal_data')
@validate_twilio_request
def save_goal_data():
	"""Saves data at the end of the Daily goal setting chat."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
		now = datetime.datetime.now()
		message_body['time'] = now

		# Dump the history (into dicts).
		history = message_body['history']
		message_body['history'] = json.dumps(history)


		logging.info("history: %s", history)


		flow_datum = GoalFlowDatum(**message_body)
		db.session.add(flow_datum)
		db.session.commit()

		return jsonify({'message': f'Flow data saved.'})
	except Exception as e:
		return jsonify({'error': str(e)})


@app.post('/save_user_feedback')
@validate_twilio_request
def save_user_feedback():
	"""Saves feedback from the user at the end of the skill."""

	message_body = request.json

	# Get the current time.
	now = datetime.datetime.now()
	message_body['time'] = now

	user_feedback_datum = UserFeedbackDatum(**message_body)
	db.session.add(user_feedback_datum)
	db.session.commit()

	return jsonify({'message': 'User data feedback saved.'})

@app.post('/sphere_of_influence/save_control_data')
@validate_twilio_request
def save_control_data():
	"""Saves data at the end of the Spheres of Influence chat."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
		now = datetime.datetime.now()
		message_body['time'] = now

		# Dump the history (into dicts).
		history = message_body['history']
		message_body['history'] = json.dumps(history)

		logging.info("history: %s", history)


		flow_datum = ControlFlowDatum(**message_body)
		db.session.add(flow_datum)
		db.session.commit()

		return jsonify({'message': f'Flow data saved.'})
	except Exception as e:
		return jsonify({'error': str(e)})

@app.post('/new_user')
def new_user():
	"""Adds new users to the user DB: receives a webhook from Wix."""

	# These key's can be found within the Wix automations;
	# there is an option to see the data structure.
	message_body = request.json['data']
	if 'field:comp-lipwozdh' in message_body:	
		user_number = message_body['field:comp-lipwozdh']
	else: 
		user_number = message_body['field:comp-ll3zlzex1']
	
	if 'field:comp-like94pe' in message_body:
		user_email = message_body['field:comp-like94pe']
	else:
		user_email = message_body['field:comp-ll3zlzeo']

	if 'contact.Id' in message_body:
		user_wix_id = message_body['contact.Id']
	else:
		user_wix_id = 'none'

	# Post-process the user number.
	if user_number:
		# Only add data if the user has provided a number

		# From (+44) 7479812734 -->   whatsapp:+447479812734
		user_number = user_number.replace('(', '')
		user_number = user_number.replace(')', '')
		# user_number = user_number.replace(' ', '')
		code, number = user_number.split(' ')
		if number.startswith('0'):
			number = number.lstrip('0')
		user_number = f'whatsapp:{code}{number}'

		# The data: giving everyone 30 tokens.
		data = dict(
			user_number=user_number,
			user_email=user_email,
			user_wix_id=user_wix_id,
			expiry_date=None,
			)

		# Check if there is already an entry for this person:
		record = db.session.query(ProfileDatum).filter(ProfileDatum.user_email == user_email).first()

		logging.info("[RECORD] %s", record)

		if record:
			record.user_number = user_number
			db.session.commit()

		else:
			profile_datum = ProfileDatum(**data)
			db.session.add(profile_datum)
			db.session.commit()

		# Add contact to EmailOctopus
		api_key = str(os.environ['EMAIL_OCTOPUS_API_KEY']).strip()

		headers = {
			'Content-Type': 'application/json',
		}

		data = (
			'{"api_key":'
			f'"{api_key}",'
			f'"email_address": "{user_email}",'
			'"status":"SUBSCRIBED"}'
			)

		list_id = "6a120b2e-2c6a-11ee-b889-9147f389737a"
		response = requests.post(f'https://emailoctopus.com/api/1.6/lists/{list_id}/contacts', headers=headers, data=data)
                
		response_dict = json.loads(response.text)
		logging.info(response_dict)
		logging.info('Request to EmailOctopus: %s', str(response.status_code))

	return jsonify({'message': message_body, 'eo_response':response_dict})

@app.post('/reminder')
def reminder():
	return reminders.reminder(request=request, db=db, UserDatum=UserDatum, ReminderDatum=ReminderDatum)

@app.post('/challenge/get_streak_infographic')
@validate_twilio_request
def get_streak_infographic():
	return challenge.get_streak_infographic(request=request, db=db, UserDatum=UserDatum)

########## Boundaries Journey ########
@app.post('/boundaries_journey/stage1/get_quiz_infographic')
@validate_twilio_request
def get_quiz_infographic():
	return boundaries.get_quiz_infographic(request=request)

@app.post('/boundaries_journey/stage1/save_data')
@validate_twilio_request
def save_boundaries_stage1_data():
	# Retrieve data from the request sent by Twilio
	return boundaries.save_stage1_data(request=request, db=db, BoundariesStageOneDatum=BoundariesStageOneDatum)

@app.post('/boundaries_journey/stage2/resentmemt_loop')
@validate_twilio_request
def resentmemt_loop():
	# Retrieve data from the request sent by Twilio
	return boundaries.resentmemt_loop(request=request)


if __name__ == "__main__":
	app.run(debug=True, use_debugger=True, port=8000)