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
import re

import create_post

# Import features.
from features import sphere_of_influence


from absl import flags

_WELCOME_TEXT = ""

_ASK_FOR_EVENT_TEXT = """To start off, please tell be about a specific challenge or issue you'd like to focus on today, something that's been on your mind?"""

_OUTSIDE_SYSTEM_PROMPT = """The assistant is guiding the user step-by-step through the outer ring of the Sphere of Influence.

The user has shared what they are worried about and the assistant must ask short questions to help the user identify the things that are in the outer circle; things that are outside of their control.

After a few turns the assistant must respond "STEP COMPLETE"."""

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
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	next_question = model_output['choices'][0]['message']['content']

	# Check if there is an event detected.
	is_done = True if 'STEP COMPLETE' in next_question else False

	# If there is no question in "next_question" also set is_done to True.
	if '?' not in next_question:
		is_done = True

	if not is_done:
		# If the conversation is not done, add the question to the history.
		history.append({"role": "assistant", "content": next_question})
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)


_SUMMARISE_OUTSIDE_SYSTEM_PROMPT = """The assistant is guiding the user step-by-step through the outer ring of the Sphere of Influence - the things the user cannot control.

The assistant has helped the user discover what they cannot control. The assistant must help the user let go with a short simple response.

The assistant must not ask a question."""

_MAX_RETRIES = 5

_DEFAULT_SUMMARY = """It can be challenging when you feel like you have little control over your tasks and responsibilities. Sometimes, it can help to let go of the things we cannot control and focus on what we can control."""

def _remove_questions(text):
	sentences = re.split(r'(?<=[.!?]) +', text)  # Split the text into sentences
	non_question_sentences = [sentence for sentence in sentences if not sentence.endswith("?")]
	result = ' '.join(non_question_sentences)
	return result

def summarise_outside(request):
	"""Summarise what is outside of the users control."""

	# Get the inputs.
	message_body = request.json
	user_event = message_body['user_event']
	history = message_body['history']
	last_user_response = message_body['last_user_response']

	messages = [
	{'role': 'system', 'content': _SUMMARISE_OUTSIDE_SYSTEM_PROMPT},
	{'role': 'assistant', 'content': _ASK_FOR_EVENT_TEXT},
	{'role': 'user', 'content': user_event},
	*history
	]

	messages.append({'role': 'user', 'content': last_user_response})

	model_output = utils.chat_completion(
		model='gpt-3.5-turbo-0613',
		messages=messages,
		max_tokens=1024,
		temperature=0.5,  # Low temp -- close to being deterministic!
		)

	response = model_output['choices'][0]['message']['content']

	# Remove any questions from the output.
	response = _remove_questions(response)

	if response:
		return jsonify(response=response)

	logging.warn(f'Question detected in response:\n{response}')
	return jsonify(response=_DEFAULT_SUMMARY)


_INSIDE_SYSTEM_PROMPT = """The assistant is guiding the user step-by-step through the inner ring of the Sphere of Influence.

The user has shared what they are worried about and the assistant must ask short questions to help the user identify the things that are in the inner circle; things that they can control.

After a few turns the assistant must respond "STEP COMPLETE"."""

def inside_loop(request):
	"""Identifies what is outside the users control."""

	# Get the inputs.
	message_body = request.json
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

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	next_question = model_output['choices'][0]['message']['content']

	# Check if there is an event detected.
	is_done = True if 'STEP COMPLETE' in next_question else False

	# If there is no question in "next_question" also set is_done to True.
	if '?' not in next_question:
		is_done = True

	if not is_done:
		# If the conversation is not done, add the question to the history.
		history.append({"role": "assistant", "content": next_question})
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)
