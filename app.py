"""The Flask App to act as an API for our Twilio app. 

These functions can be used later too in the final product.
"""
from flask import Flask, jsonify, request
from abc_types import Sentiment
import json
import logging
from utils import dummy_call_api as call_api
import copy

app = Flask(__name__)

OUT_DATA_PATH = 'data/gpt_outputs'

@app.route('/')
def hello():
	return 'Hello, World!'


# The feeling prompt: Expected output is of the form:
# < NEG | POS | NEURTRAL >
# <feeling> feeling_1, feeling_2, ... </feeling>.
_FEELING_PROMPT = """
For the following sentence please response with POS is the sentiment is positive, NEG if the sentiment is negative and NEUTRAL if the sentiment is neutral.  Then on the next line write <feelings> followed by a list of one word feelings expressed by the use, end this with </feeling>. If the sentence also includes an event include then on the next line write <event> followed by the event that was described, end this with </event>. The event should be described in the second person and be a complete sentence. "{feeling}"
"""

def feelings_post_process(model_output: str):
	"""Post processing for the _FEELING_PROMPT prompt."""

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
	feelings = None
	model_output_ = copy.copy(model_output)
	if '<feelings>' in model_output_:
		model_output_ = model_output_.split('<feelings>')[1]
		if '</feelings>' in model_output_:
			model_output_ = model_output_.split('</feelings>')[0]
			feelings = [
				f.lower().strip()for f in model_output_.split(',')]
		else:
			logging.warning('No </feelings> key detected in %s.',
				model_output_)
	else:
		logging.warning('No <feelings> key detected in %s.',
			model_output_)

	# If there is an event, get the event.
	event = None
	model_output_ = copy.copy(model_output)
	if '<event>' in model_output_:
		model_output_ = model_output_.split('<event>')[1]
		if '</event>' in model_output_:
			model_output_ = model_output_.split('</event>')[0]
			event = model_output_.lower().strip()
		else:
			logging.warning('No </event> key detected in %s.',
				model_output)
	else:
		logging.warning('No <event> key detected in %s.',
			model_output)


	return dict(
		sentiment=sentiment, feelings=feelings, event=event)

@app.post('/feeling')
def user_feeling():
	"""Response to: How are you feeling today?"""

	# Retrieve data from the request sent by Twilio
	data = request.get_json()
	message_body = data.get('Body')

	# Create the feelings prompt.
	prompt = _FEELING_PROMPT.format(
		feeling=message_body['feeling'])

	# Call to the LLM
	# TODO(toni) Call the LLM
	model_output = call_api(
		origin='user_feeling',
		out_dir=OUT_DATA_PATH)
	model_output = model_output['choices'][0]['text']

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


if __name__ == "__main__":
	app.run(debug=True, use_debugger=True, port=8000)