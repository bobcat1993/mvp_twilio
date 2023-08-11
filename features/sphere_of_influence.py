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

import create_post

# Import features.
from features import sphere_of_influence


from absl import flags

_WELCOME_TEXT = ""

_ASK_FOR_EVENT_TEXT = """To start off, please tell be about a specific challenge or issue you'd like to focus on today, something that's been on your mind?"""

_OUTSIDE_OF_CONTROL_SYSTEM_PROMPT = """The assistant is guiding the user step-by-step through the outer ring of the Sphere of Influence.

The user has shared what they are worried about and the assistant must ask short questions to help the user identify the things that are in the outer circle; things that are outside of their control.  The assistant must break it down for the user where possible.

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
	{"role": "system", "content": _OUTSIDE_OF_CONTROL_SYSTEM_PROMPT},
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
