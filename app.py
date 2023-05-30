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
from utils import dummy_call_api as call_api
import utils
import copy
import os
import openai

# Set up the openai LLM client.
openai.organization = "org-PIBY8HetnWz6gzQASJ8TOy8d"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()

app = Flask(__name__)

OUT_GPT_DATA_PATH = 'data/gpt_outputs'
OUT_FLOW_DATA_PATH = 'data/flow_outputs'

@app.route('/')
def hello():
	return 'Hello, World!'


# The feeling prompt: Expected output is of the form:
# < NEG | POS | NEURTRAL >
# <feeling> feeling_1, feeling_2, ... </feeling>.
_FEELING_PROMPT = """
For the following sentence please response with POS is the sentiment is positive, NEG if the sentiment is negative and NEUTRAL if the sentiment is neutral.  Then on the next line write <feelings> followed by a list of one word feelings expressed by the use, end this with </feelings>. If the sentence also includes an event include then on the next line write <event> followed by the event that was described, end this with </event>. The event should be described in the second person and be a complete sentence. "{feeling}".
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

	# Get the feelings.
	feelings = utils.post_process_tags(model_output, 'feelings')
	if feelings:
		# If not None, feelings needs to be a list of feelings.
		feelings = [f.strip().lower() for f in feelings.split(',')]

	# If there is an event, get the event.
	event = utils.post_process_tags(model_output, 'event')
	if event:
		event = event.lower()

	return dict(
		sentiment=sentiment, feelings=feelings, event=event)


@app.post('/feeling_test')
def user_feeling_test():
	"""TEST Response to: How are you feeling today?"""
	# Prepare the response.
	# TODO(toni) Format feelings into a feelings string.
	response = {
		'sentiment': Sentiment.NEG.value, 
		'feelings': ['sad', 'angry'],
		'event': 'had an argument with a friend'
	}

	# Return a JSON response
	return jsonify(response)

@app.post('/feeling')
def user_feeling():
	"""Response to: How are you feeling today?"""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	logging.info("message_body:", message_body)

	# Create the feelings prompt.
	# The "feeling" key comes from the http_feeling widget on the Twilio side.
	prompt = _FEELING_PROMPT.format(
		feeling=message_body['feeling'])

	# Call to the LLM
	# TODO(toni) Call the LLM
	model_output = call_api(
		origin='user_feeling',
		out_dir=OUT_GPT_DATA_PATH)
	model_output = model_output['choices'][0]['message']['content']

	# Post-process the output to get the sentiment and feelings.
	response = feelings_post_process(model_output)

	# Prepare the response.
	# TODO(toni) Format feelings into a feelings string.
	response = {
		# TODO(toni) REPLACE WITH: response['sentiment'],
		'sentiment': Sentiment.POS.value, 
		# TODO(toni) REPLACE WITH: response['feelings']
		'feelings': 'good',
		'event': response['event']
	}

	# Return a JSON response
	return jsonify(response)


_DISTORTION_DETECTION_PROMPT = """
For the following sentence you need to identify the distortions in the users thinking and pose a question to help them realise that distortion. For distortion question pair you must start on a new line with the key <distortion> followed by the distortion, end this with </distortion>. Then on the next line write <question> followed by a question that would help someone identify the distortion, end this with </question>. The question should not directly reference the distortion and should be relevant to the original sentence. "{belief}."
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
def detect_distortions():
	"""Detect distortions in the users belief."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Create the feelings prompt.
	# The "belief" key comes from the http_detect_distortions widget on the Twilio side.
	prompt = _DISTORTION_DETECTION_PROMPT.format(
		belief=message_body['belief'])

	# Call to the LLM
	# TODO(toni) Call the LLM
	model_output = call_api(
		origin='detect_distortions',
		out_dir=OUT_GPT_DATA_PATH)
	model_output = model_output['choices'][0]['message']['content']

	# The model may have recognised several distortions (separated by '\n\n').
	# For now just take one of these.
	# TODO(toni) Use all of the distortions.
	model_output = model_output.split('\n\n')[0]

	# Post process the response to get the distortion and question to ask the user.
	response = distortion_detection_post_processing(model_output)

	return jsonify(response)


@app.post('/save_abc_data')
def save_abc_data():
	"""Saves data at the end of the ABC chat."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json
		# Save the data
		json_object = json.dumps(message_body, indent=2)
		path = os.path.join(OUT_FLOW_DATA_PATH, 'flow_response.json')
		with open(path, "a") as outfile:
			outfile.write(json_object)

		return jsonify({'message': 'Data saved'})
	except Exception as e:
		return jsonify({'error': str(e)})


if __name__ == "__main__":
	app.run(debug=True, use_debugger=True, port=8000)