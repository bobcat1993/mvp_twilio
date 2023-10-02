"""Functions for the burnout survey"""
from hashlib import md5
from flask import jsonify
from google.cloud import storage
import matplotlib.pyplot as plt
import re
import os
from datetime import datetime, timedelta
from google.auth import compute_engine
import json
from absl import logging

_COLORS = '#F598FF', '#CCCCFF', '#E5E9FD', '#171D3A'

_MAX_BURNOUT_SCORE = 5


def get_BurnoutSurveyDatum(db):
	class BurnoutSurveyDatum(db.Model):
		"""Stores the data Burnout-Survey flow."""

		id = db.Column(db.Integer, primary_key=True)
		results = db.Column(db.String, nullable=True)
		flow_sid = db.Column(db.String, nullable=True)
		origin = db.Column(db.String, nullable=True)
		user_id = db.Column(db.String, nullable=True)
		error = db.Column(db.String, nullable=True)
		time = db.Column(db.DateTime, nullable=True)

	return BurnoutSurveyDatum

# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()

def get_burnout_infographic(request):

	# Get the inputs.
	message_body = request.json

	# Get the list of results.
	results = message_body['results']
	user_id = string_hash(message_body['user_number'])

	# Count up the score.
	def get_score(x):
		"""Get the score as an int from the string."""
		if x is None:
			return None
		# Take the first number we find.
		scores = re.findall(r'\d+', x)
		if scores:
			return int(scores[0])
		else:
			return None

	scores = [get_score(s) for s in results]   # Get the integer score.
	scores = [s for s in scores if s != None]  # Remove any Nones.

	percent_burnout = float(sum(scores)) / (_MAX_BURNOUT_SCORE * len(scores))

	# TODO: Make the title depending on the score.
	title = 'Bobby can help you reduce your risk of burnout'
	if percent_burnout > 0.8:
		# User mostly responding with "often"/"always"
		title = 'I\'m sorry that you are having a difficult time at the moment. Bobby can teach you skills to help you manage workplace stress and improve your wellbeing. However, if how you are feeling about your work is significantly affecting your mood, your ability to look after yourself or your performance at work, please seek help from a professional. You can find some helpful links on our website, bobby-chat.com/help.'
	elif percent_burnout > 0.6:
		# User mostly responding with "sometimes"/"often"
		title = 'I\'m sorry that you are having a tough time at the moment. Bobby can teach you skills to help you manage workplace stress and improve your wellbeing.However, if how you are feeling about your work is significantly affecting your mood, your ability to look after yourself or your performance at work, please seek help from a professional. You can find some helpful links on our website, bobby-chat.com/help.'
	elif percent_burnout > 0.4:
		# User mostly responding with "rarely"/"sometimes"
		title = 'It sounds like sometimes you could do will a little extra help to manage your work stress. The good news is, Bobby can help you with that and hopefully help you improve your wellbeing score over time. However, if how you are feeling about your work is significantly affecting your mood, your ability to look after yourself or your performance at work, please seek help from a professional. You can find some helpful links on our website, bobby-chat.com/help.'
	elif percent_burnout > 0.2:
		# User mostly responding with "never" / "rarely"
		title = 'It sounds like most of the time you are able to cope well at work, that\'s great. Bobby can help you in those isolated moments and can help you practice techniques to boost your confidence and help you set goals at work.'
	else:
		title = 'It sounds like most of the time you are able to cope well at work, that\'s great. Bobby can help you practice techniques to boost your confidence and help you set goals at work.'



	# Unique file name for each user.
	path = f'{user_id}.png'
	temp_path = path

	# Compute wellbeing score as 1 - the burnout.
	wellbeing_score = 1 - percent_burnout

	# Create the values and labels.
	val = [percent_burnout, wellbeing_score]
	label = ['', '']

	# Plot.
	fig = plt.figure(figsize=(6,6), dpi=150)
	ax = fig.add_subplot(1,1,1)
	ax.pie(val, labels=label, colors=['#F598FF', '#CCCCFF'])
	ax.add_artist(plt.Circle((0, 0), 0.6, color='white'))
	ax.set_title(f'Your wellbeing score is {int(wellbeing_score * 100)} / 100', wrap=True)
	fig.savefig(temp_path)


	api_key = os.environ['GOOGLE_API_KEY']
	client = storage.Client(project='bobby-chat', client_options={"api_key": api_key})
	bucket = client.get_bucket('bobby-chat-survey')
	blob = bucket.blob(f'temp/{path}')  
	blob.upload_from_filename(f'{temp_path}', content_type='image/png')

	# Create a signed URL so that the data can only be accessed long 
	# enough to share the image.
	storage_client = storage.Client.from_service_account_json(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
	image_url = blob.generate_signed_url(
		expiration=timedelta(hours=1),
		client=storage_client)


	# This URL is not needed anymore.
	# TODO(toni) Remove in future CL.
	# image_url = f'https://storage.googleapis.com/bobby-chat-survey/temp/{path}'

	# Remove the local image once done.
	os.remove(temp_path)

	return jsonify(
		percent_burnout=percent_burnout,
		wellbeing_score=wellbeing_score,
		image_url=image_url,
		title=title)




def save_burnout_survey_data(request, db, BurnoutSurveyDatum):
	"""Saves data from the burnout survey."""
	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Hash the user_id so that the data is pseudo-anonyms.
	message_body['user_id'] = string_hash(message_body['user_number'])

	# Remove the user_number.
	message_body.pop('user_number')

	# Get the current time.
	now = datetime.now()
	message_body['time'] = now

	# Dump the history (into dicts).
	results = message_body['results']
	message_body['results'] = json.dumps(results)

	logging.info("results: %s", results)

	datum = BurnoutSurveyDatum(**message_body)
	db.session.add(datum)
	db.session.commit()

	return jsonify({'message': f'Flow data saved.'})