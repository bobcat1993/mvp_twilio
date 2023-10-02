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


# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()


_ASK_FOR_EVENT_TEXT = """To start off, please tell be about a specific challenge or issue you'd like to focus on today, something that's been on your mind?"""

# TODO(toni) Move to utils.py file,
def _remove_questions(text):
	sentences = re.split(r'(?<=[.!?]) +', text)  # Split the text into sentences
	non_question_sentences = [sentence for sentence in sentences if not sentence.endswith("?")]
	result = ' '.join(non_question_sentences)
	return result


_CONTROL_LOOP_SYSTEM_PROMPT = """The kind and friendly assistant is guiding the user step-by-step through the the Sphere of Influence.

The user has shared a specific challenge or situation that they would like help with. 

First, the assistant must ask short questions to help the user identify two things that they cannot control in this situation and encourage them to let go of those things.

Next, the assistant must ask short questions to help the user identify at least two things that they can control in that situation and help them to focus their efforts and energy there.

The assistant always asks kind, short questions and always takes the side of the user. The assistant should also recognise that there may be systematic biases that make it harder for some users to have control.

When the session ends the assistant must respond "SESSION COMPLETE" ."""

def control_loop(request):
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
	{"role": "system", "content": _CONTROL_LOOP_SYSTEM_PROMPT},
	{"role": "assistant", "content": _ASK_FOR_EVENT_TEXT},
	{"role": "user", "content": user_event},
	*history
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
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