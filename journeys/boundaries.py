"""The Boundaries Journey"""
from flask import jsonify, request
from absl import logging
import json
import sys
from google.cloud import storage
import datetime
from hashlib import md5
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import io
import tempfile
import re

sys.path.append('..')
import utils

load_dotenv()

_COLORS = '#F598FF', '#CCCCFF', '#E5E9FD', '#171D3A'


def get_BoundariesStageOneDatum(db):
	class BoundariesStageOneDatum(db.Model):
		"""Stores the data Boundaries-Stage1 flow."""

		__tablename__ = 'boundaries_stage_one_datum'

		id = db.Column(db.Integer, primary_key=True)
		results = db.Column(db.String, nullable=True)
		user_feel_after = db.Column(db.String, nullable=True)
		flow_sid = db.Column(db.String, nullable=True)
		origin = db.Column(db.String, nullable=True)
		user_id = db.Column(db.String, nullable=True)
		error = db.Column(db.String, nullable=True)
		time = db.Column(db.DateTime, nullable=True)
		time_spent_on_video = db.Column(db.DateTime, nullable=True)

	return BoundariesStageOneDatum


def get_BoundariesStageTwoDatum(db):
	class BoundariesStageTwoDatum(db.Model):
		"""Stores the data Boundaries-Stage2 flow."""

		__tablename__ = 'boundaries_stage_two_datum'

		id = db.Column(db.Integer, primary_key=True)
		history = db.Column(db.String, nullable=True)
		user_event = db.Column(db.String, nullable=True)
		last_bot_response = db.Column(db.String, nullable=True)
		user_boundary = db.Column(db.String, nullable=True)
		user_feel_after = db.Column(db.String, nullable=True)
		flow_sid = db.Column(db.String, nullable=True)
		origin = db.Column(db.String, nullable=True)
		user_id = db.Column(db.String, nullable=True)
		error = db.Column(db.String, nullable=True)
		time = db.Column(db.DateTime, nullable=True)
		time_spent_on_video = db.Column(db.DateTime, nullable=True)

	return BoundariesStageTwoDatum


# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()

# TODO(toni) Add this to a utils.py file.
def _remove_questions(text):
	sentences = re.split(r'(?<=[.!?]) +', text)  # Split the text into sentences
	non_question_sentences = [sentence for sentence in sentences if not sentence.endswith("?")]
	result = ' '.join(non_question_sentences)
	return result


####### STAGE 1 ######
def get_quiz_infographic(request):

	# Get the inputs.
	message_body = request.json

	# Get the list of results.
	results = message_body['results']
	user_id = string_hash(message_body['user_number'])

	# Count the "Yes"s and the "No"s.
	results = [r.lower() for r in results]
	results = ['yes' if 'yes' in r else r for r in results]
	results = ['no' if 'no' in r else r for r in results]
	num_yes = results.count('yes')
	num_no = results.count('no')

	percent_yes = float(num_yes)/ len(results)

	# Make the title depending on the score.
	if percent_yes == 1.0:
		title = 'It looks like you are great at setting boundaries!\nThis series will help you refine this skill!'
	elif percent_yes >= 0.5:
		title = 'It looks like you are good at setting boundaries but could still do with a little help. This series is here for you.'
	elif percent_yes >= 0.2:
		title = 'It sounds like you are able to set some boundaries but still need some help with others.\nThis series will help you do just that!'
	else:
		title = 'It sounds like you really struggle to set boundaries, but don\'t worry. This series will help you set boundaries and even see how your boundaries can benefit those around you!'

	# Make a plot.
	label = ["Yes", "No"]
	val = [num_yes, num_no]

	# Unique file name for each user.
	path = f'{user_id}.png'
	temp_path = path

	# plot
	fig = plt.figure(figsize=(6,6), dpi=150)
	ax = fig.add_subplot(1,1,1)
	ax.pie(val, labels=label, colors=_COLORS)
	ax.add_artist(plt.Circle((0, 0), 0.6, color='white'))
	ax.set_title('Your responses', wrap=True)
	fig.savefig(temp_path)


	api_key = os.environ['GOOGLE_API_KEY']
	client = storage.Client(project='bobby-chat', client_options={"api_key": api_key})
	bucket = client.get_bucket('bobby-chat-boundaries')
	blob = bucket.blob(f'temp/{path}')  
	blob.upload_from_filename(f'{temp_path}', content_type='image/png')


	image_url = f'https://storage.googleapis.com/bobby-chat-boundaries/temp/{path}'

	# Remove the image once done.
	os.remove(temp_path)

	return jsonify(
		num_yes=num_yes,
		num_no=num_no,
		image_url=image_url,
		title=title)

def save_stage1_data(request, db, BoundariesStageOneDatum):
	"""Saves data at the end of stage 1 of the boundaries journey."""
	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Hash the user_id so that the data is pseudo-anonyms.
	message_body['user_id'] = string_hash(message_body['user_id'])

	# Get the current time.
	now = datetime.datetime.now()
	message_body['time'] = now

	# Dump the history (into dicts).
	results = message_body['results']
	message_body['results'] = json.dumps(results)

	logging.info("results: %s", results)

	datum = BoundariesStageOneDatum(**message_body)
	db.session.add(datum)
	db.session.commit()

	return jsonify({'message': f'Flow data saved.'})



####### STAGE 2 #######
_FOLLOW_THE_RESENTMENT_SYSTEM_PROMPT = """
In this coaching session, the assistant is going to guide the user through the "Follow The Resentment" exercise. On every turn the assistant asks short, friendly questions. 

First the assistant will ask the user to identify a situation where they felt some resentment. For example, did the user say yes to something  that they later wish they had said no to.

Then the assistant will dig deeper to understand what is pushing the users buttons, how they responded in the moment, what the user wishes they had done differently and finally, where the users wants to feel more boundaried in this situation.

The assistant asks short, friendly questions. Once the user has identified where they want to be more boundaried the assistant will respond "SESSION FINISHED"."""

_ASSISTANT_ASK_FOR_RESENTMENT = """It's not always easy to see where your boundaries are being pushed. I'm going to help you "follow the resentment" to figure out where your boundaries may have been pushed. To get started, can you think of a recent situation where you felt some resentment?"""

_FINAL_RESETMENT_TURN = """Well done for "following the resentment" to identify where your boundaries are being pushed."""

MAX_RESETMENT_STEPS = 30
MIN_RESETMENT_STEPS = 15

def resentmemt_loop(request):
	"""Gets the user to Follow the Resentment to identify where their boundaries have been pushed."""

	# Get the inputs.
	message_body = request.json
	history = message_body['history']
	user_event = message_body['user_event']
	current_user_response = message_body['last_user_response']

	# Add the previous user response to the end of the history.
	if current_user_response:
		history.append({"role": "user", "content": current_user_response})

	messages = [
	{"role": "system", "content": _FOLLOW_THE_RESENTMENT_SYSTEM_PROMPT},
	{"role": "assistant", "content": _ASSISTANT_ASK_FOR_RESENTMENT},
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
	# Warning: This is the raw next question. If this is the last step it will include 'SESSION FINISHED'.
	history.append({"role": "assistant", "content": next_question})

	# Check if there is an event detected.
	is_done = True if 'SESSION FINISHED' in next_question else False

	if len(messages) == MAX_RESETMENT_STEPS:
		app.logger.warn(f'is_done != True, but has reached {MAX_CHEER_STEPS} messages.')
		is_done = True

	if is_done:
		next_question = next_question.split('SESSION FINISHED')[0]
		next_question = next_question.strip(' .\n')
		next_question = _remove_questions(next_question)

	# If there is no question in "next_question" also set is_done to True.
	if ('?' not in next_question) and (len(messages) > MIN_RESETMENT_STEPS):
		is_done = True

	if next_question == '':
		next_question = _DEFAULT_FINAL_RESETMENT_TURN
	
	return jsonify(
		is_done=is_done,
		question=next_question,
		history=json.dumps(history),  # Be sure to dump!!
		messages=messages,
	)


def save_stage2_data(request, db, BoundariesStageTwoDatum):
	"""Saves data at the end of stage 2 of the boundaries journey."""
	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Hash the user_id so that the data is pseudo-anonyms.
	message_body['user_id'] = string_hash(message_body['user_id'])

	# Get the current time.
	now = datetime.datetime.now()
	message_body['time'] = now

	# Dump the history (into dicts).
	history = message_body['history']
	message_body['history'] = json.dumps(history)

	datum = BoundariesStageTwoDatum(**message_body)
	db.session.add(datum)
	db.session.commit()

	return jsonify({'message': f'Flow data saved.'})