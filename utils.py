"""Util. functions."""

import json
import os
import logging

import openai
from dotenv import load_dotenv
from twilio.request_validator import RequestValidator
from functools import wraps
from flask import request
from flask import abort, current_app, request

load_dotenv()

# Set up the openai LLM client.
def setup_openai():
	openai.organization = "org-PIBY8HetnWz6gzQASJ8TOy8d"
	openai.api_key = os.getenv("OPENAI_API_KEY")
	return openai.Model.list()

def dummy_call_api(
	origin: str,
	out_dir: str,
	model="dummy-model",  # gpt-3.5-turbo
	prompt="Say this is a test",
	max_tokens=7,
	temperature=0,
	) -> str :
	"""Calls a dummy API.

	Save the response to OUT_DATA_PATH/{origin}-{xid}

	Args:
		origin: The origin of the api call.
		out_dir: The directory to save the response.
		model: The openAI model.
		prompt: The prompt used.
		max_tokens: The max. number of tokens to sample.
		temperature: The sampling temp.

	Returns:
		A text response.
	"""

	response = {
		"id": "some-kind-of-id",
		"object": "text_completion",
		"created": 1589478378,
		"model": "text-davinci-003",
		"choices": [
			{
				"text": "\n\nThis is indeed a test",
				"index": 0,
				"logprobs": None,
				"finish_reason": "length"
			}
		],
		"usage": {
			"prompt_tokens": 5,
			"completion_tokens": 7,
			"total_tokens": 12
		},
		"origin": origin,
		"prompt": prompt,
		"temperature": temperature,
		"max_tokens": max_tokens
	}

	# Save the response.
	# We want to save all responses so that we have a clear record of what's been
	# tried so far.
	# json_object = json.dumps(response, indent=2)
	# path = os.path.join(out_dir, 'dummy_api_calls.json')
	# with open(path, "a") as outfile:
	# 	outfile.write(json_object)


	# TODO(toni) Check finish reason! Needs to be "stop" not "length".
	return "\n\nThis is indeed a test"


def call_api(
	origin: str,
	out_dir: str,
	prompt: str,
	model="gpt-3.5-turbo",
	max_tokens=1024,
	temperature=1,
	) -> str:
	"""Call the OpenAI API to get a response.

	Args:
		origin: Which function is this api being called from?
		out_dir: Where to save the response. We always want to save
			responses to keep track of things we have tried.
		prompt: The input prompt to the model.
		model: The chat model we want to use.
		max_tokens: The max tokens we want to sample.
		temperature: The temperature to sample with, default to 1. Lower
			values are more stochastic, values close to one are more
			deterministic.

	Returns:
		A text response.
	"""
	setup_openai()

	response = openai.ChatCompletion.create(
		model=model,
		messages=[
			{"role": "system", "content": "You are a helpful assistant."},
			{"role": "user", "content": prompt}],
		max_tokens=max_tokens,
		temperature=temperature,
		)


	# Add additional info
	input_info = {
		"origin": origin,
		"prompt": prompt,
		"temperature": temperature,
		"max_tokens": max_tokens
		}
	response.update(input_info)

	# Save the response.
	# We want to save all responses so that we have a clear record of what's been
	# tried so far.
	json_object = json.dumps(response, indent=2)
	path = os.path.join(out_dir, 'openai_api_calls.json')
	with open(path, "a") as outfile:
		outfile.write(json_object)

	# TODO(toni) Check finish reason! Needs to be "stop" not "length".
	return response['choices'][0]['message']['content']


def post_process_tags(text: str, tag: str):
	"""Extracts text from between <tag> and </tag>.

	Args:
		text: The input text.
		tag: The tag without the <>.

	Returns:
		The text between the tags. For example if text=<tag> and </tag>,
		the function returns "and".
	"""

	output = None
	if f'<{tag}>' in text:
		text = text.split(f'<{tag}>')[1]
		if f'</{tag}>' in text:
			return text.split(f'</{tag}>')[0].strip('. ')
		else:
			logging.warning('No </%s> key detected in %s.',
				tag, text)
	else:
		logging.warning('No <%s> key detected in %s.',
			tag, text)

def validate_twilio_request(f):
	"""Validates that incoming requests genuinely originated from Twilio"""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		# Create an instance of the RequestValidator class
		validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

		# Validate the request using its URL, POST data,
		# and X-TWILIO-SIGNATURE header
		request_valid = validator.validate(
			request.url,
			request.form,
			request.headers.get('X-TWILIO-SIGNATURE', ''))

		# Continue processing the request if it's valid (or if DEBUG is True)
		# and return a 403 error if it's not
		if request_valid or current_app.debug:
			return f(*args, **kwargs)
		else:
			return abort(403)
	return decorated_function



