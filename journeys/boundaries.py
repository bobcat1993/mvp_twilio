"""The Boundaries Journey"""
from flask import jsonify, request
from absl import logging
import pygal
from google.cloud import storage
import datetime
from hashlib import md5
from dotenv import load_dotenv
import os

load_dotenv()

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
	results = ['yes' if 'yes' in r else 'no' for r in results]
	num_yes = float(results.count('yes'))
	num_no = float(results.count('no'))

	# Make the title depending on the score.
	if num_yes == 0:
		title = 'It looks like you are great at setting boundaries!\nThis series will help you refine this skill!'
	elif num_yes/num_no <= 0.2:
		title = 'It looks like you are good at setting boundaries but could still do with a little help. This series is here for you.'
	elif num_yes/num_no <= 0.5:
		title = 'It sounds like you are able to set some boundaries but still need some help with others.\nThis series will help you do just that!'
	else:
		title = 'It sounds like you really struggle to set boundaries, but don\'t worry. This series will help you set boundaries and even see how your boundaries can benefit those around you!'

	# Make a plot.
	pie_chart = pygal.Pie(half_pie=True)
	pie_chart.title = title
	pie_chart.add('Yes', num_yes)
	pie_chart.add('No', num_no)
	pie_chart.add('Other', len(results) - (num_yes + num_no))
	svg_bytes = pie_chart.render(is_unicode=True)

	# Save the plot
	# init GCS client and upload buffer contents
	api_key = os.environ['GOOGLE_API_KEY']
	client = storage.Client(project='bobby-chat', client_options={"api_key": api_key})
	bucket = client.get_bucket('bobby-chat-boundaries')
	blob = bucket.blob(f'{user_id}_.svg')  
	blob.upload_from_string(svg_bytes, content_type='image/svg')

	return jsonify(
		num_yes=num_yes,
		num_no=num_no)