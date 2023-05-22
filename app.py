"""The Flask App to act as an API for our Twilio app. 

These functions can be used later too in the final product.
"""
from flask import Flask, jsonify, request
import abc_types
import json

app = Flask(__name__)

OUT_DATA_PATH = 'data/gpt_outputs'


def call_api(
	origin: str,
	model="dummy-model",  # gpt-3.5-turbo
	prompt="Say this is a test",
  max_tokens=7,
  temperature=0,
  ):
	"""Dummy API call.

	Save the response to OUT_DATA_PATH/{origin}-{xid}

	Args:
		origin: The origin of the api call.
		model: The openAI model.
		prompt: The prompt used.
		max_tokens: The max. number of tokens to sample.
		temperature: The sampling temp.

	Returns:
		A json.
	"""

	response = {
		"id": "some-kind-of-id",
		"object": "text_completion",
		"created": 1589478378,
		"model": "dummy-model",
		"choices": [
		  {
		  "text": "\n\nThis is indeed a test",
			"index": 0,
			"logprobs": null,
			"finish_reason": "length"
		  }
		],
		"usage": {
			"prompt_tokens": 5,
			"completion_tokens": 7,
			"total_tokens": 12
		}
	}
	return response


@app.route('/')
def hello():
	return 'Hello, World!'


# The feeling prompt: Expected output is of the form:
# < NEG | POS | NEURTRAL >
# <feeling> feeling_1, feeling_2, ... </feeling>.
_FEELING_PROMPT = """
For the following sentence please response with POS if the sentiment is positive, NEG if the sentiment is negative and NEUTRAL if the sentiment is neutral.  Then on the next line write <feelings> followed by a list of one word feelings expressed by the user, end this with </feeling>. "{feeling}"
"""

@app.post('/feeling')
def user_feeling():
	"""Response to: How are you feeling today?"""

	# Retrieve data from the request sent by Twilio
	data = request.get_json()
	message_body = data.get('Body')

	prompt = _FEELING_PROMPT.format(
		feeling=message_body['feeling'])


	# Prepare the response
	response = {
		'sentiment': abc_types.Sentiment.POS.value,
		'feeling': 'good'.lower(),
	}

	# Return a JSON response
	return jsonify(response)


if __name__ == "__main__":
	app.run(debug=True, use_debugger=True, port=8000)