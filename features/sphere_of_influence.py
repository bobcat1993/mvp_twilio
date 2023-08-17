"""Functions for the Sphere of Influence Feature"""
from flask import jsonify, request
import json
import logging
import utils
import copy
import os
import sys
import datetime
from hashlib import md5
from flask_sqlalchemy import SQLAlchemy
import re

import create_post

# Import features.
from features import sphere_of_influence

# create the extension
db = SQLAlchemy()

class ControlFlowDatum(db.Model):
	"""Stores the data from the SMART goal setting flow."""

	id = db.Column(db.Integer, primary_key=True)
	user_event = db.Column(db.String, nullable=True)
	outside_loop_history = db.Column(db.String, nullable=True)
	inside_loop_history = db.Column(db.String, nullable=True)
	user_feel_after = db.Column(db.String, nullable=True)
	flow_sid = db.Column(db.String, nullable=True)
	origin = db.Column(db.String, nullable=True)
	user_id = db.Column(db.String, nullable=True)
	error = db.Column(db.String, nullable=True)
	time = db.Column(db.DateTime, nullable=True)


# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()

_WELCOME_TEXT = ""

_ASK_FOR_EVENT_TEXT = """To start off, please tell be about a specific challenge or issue you'd like to focus on today, something that's been on your mind?"""

_OUTSIDE_SYSTEM_PROMPT = """The kind and friendly assistant is guiding the user step-by-step through the outer ring of the Sphere of Influence -- understanding what the user cannot control.

The user has shared a specific challenge or issue that they would like help with. The assistant must ask short questions to help the user identify the things that they cannot control in this situation and encourage them to let go of those things.

After a few turns the assistant must respond "STEP COMPLETE"."""

_DEFAULT_OUTTER_SUMMARY = """It can be challenging when you feel like you have little control over your tasks and responsibilities. Sometimes, it can help to let go of the things we cannot control and focus on what we can control."""

def _remove_questions(text):
	sentences = re.split(r'(?<=[.!?]) +', text)  # Split the text into sentences
	non_question_sentences = [sentence for sentence in sentences if not sentence.endswith("?")]
	result = ' '.join(non_question_sentences)
	return result

def outside_loop(request):
	"""Identifies what is outside the users control."""

	# Get the inputs.
	message_body = request.json
	history = message_body['history']
	user_event = message_body['user_event']
	current_user_response = message_body['last_user_response']

	# Add the previous user response to the end of the history.
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	messages = [
	{"role": "system", "content": _OUTSIDE_SYSTEM_PROMPT},
	{"role": "assistant", "content": _ASK_FOR_EVENT_TEXT},
	{"role": "user", "content": user_event},
	*history
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0631",
		messages=messages,
		max_tokens=256,
		temperature=1.0,
		)

	next_question = model_output['choices'][0]['message']['content']

	# Check if there is an event detected.
	is_done = True if 'STEP COMPLETE' in next_question else False

	if is_done:
		next_question = next_question.replace('STEP COMPLETE', '')
		next_question = next_question.strip('\n')
		next_question = _remove_questions(next_question)

	if not next_question:
		next_question = _DEFAULT_OUTTER_SUMMARY

	# If there is no question in "next_question" also set is_done to True.
	if '?' not in next_question:
		is_done = True

	# Add the question to the history.
	history.append({"role": "assistant", "content": next_question})
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)


_INSIDE_SYSTEM_PROMPT = """The kind and friendly assistant is guiding the user step-by-step through the inner ring of the Sphere of Influence.

The user has shared a specific challenge or situation that they would like help with. The assistant asks short questions to help the user identify the things that they can control in that situation and help them to focus their efforts and energy there.

The assistant always asks kind, short questions and always takes the side of the user. The assistant should also recognise that there may be systematic biases that make it harder for some users to have control.

Keep the session short and focused. When the session ends the assistant must respond "SESSION COMPLETE"."""

_DEFAULT_INNER_SUMMARY = """Remember, don't waste your energy on things that are outside of your control and focus your energy on the things you can control."""

def inside_loop(request):
	"""Identifies what is outside the users control."""

	# Get the inputs.
	message_body = request.json
	# The history includes the inside loop history.
	history = message_body['history']
	user_event = message_body['user_event']
	current_user_response = message_body['last_user_response']

	# Add the previous user response to the end of the history.
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	# TODO(toni) Include all the previous history!
	messages = [
	{"role": "system", "content": _INSIDE_SYSTEM_PROMPT},
	{"role": "assistant", "content": _ASK_FOR_EVENT_TEXT},
	{"role": "user", "content": user_event},
	*history
	]

	if len(history) == 0:
		# If it's the fist turn on the inner loop use a pre-written question.
		next_question = """Let's switch to focusing on what you can control. What are some of the things you feel that you can control in this situation?"""
	else:
		# If it's a any other turn use the LLM.
		model_output = utils.chat_completion(
			model="gpt-3.5-turbo-0631",
			messages=messages,
			max_tokens=256,
			temperature=1.0,
			)

		next_question = model_output['choices'][0]['message']['content']

	# Check if there is an event detected.
	is_done = True if 'SESSION COMPLETE' in next_question else False

	if is_done:
		next_question = next_question.replace('SESSION COMPLETE', '')
		next_question = next_question.strip('\n .')
		next_question = _remove_questions(next_question)

	# If there is no question in "next_question" also set is_done to True.
	if '?' not in next_question:
		is_done = True

	#Add the question to the history.
	history.append({"role": "assistant", "content": next_question})
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)

def save_control_data(request):
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
		for key in ['inside_loop_history', 'outside_loop_history']:
			history = message_body[key]
			message_body[key] = json.dumps(history)

			logging.info("%s: %s", key, history)


		flow_datum = ControlFlowDatum(**message_body)
		db.session.add(flow_datum)
		db.session.commit()

		return jsonify({'message': f'Flow data saved.'})
	except Exception as e:
		return jsonify({'error': str(e)})

