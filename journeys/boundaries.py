"""The Boundaries Journey"""
from flask import jsonify, request
from absl import logging
from google.cloud import storage
import datetime
from hashlib import md5
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import io
import tempfile
import json

load_dotenv()

_COLORS = '#F598FF', '#CCCCFF', '#E5E9FD', '#171D3A'


def get_BoundariesStageOneDatum(db):
	class BoundariesStageOneDatum(db.Model):
		"""Stores the data from the SMART goal setting flow."""

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


# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()

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
