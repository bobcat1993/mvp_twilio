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
from utils import call_api as call_api
import utils
import copy
import os


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
For the following sentence please response with POS if the sentiment is positive, NEG if the sentiment is negative and NEUTRAL if the sentiment is neutral. Then on the next line write <feelings> followed by a short (comma separated) list of one word feelings expressed in the sentence, end this with </feelings>. If the feeling is mixed pick POS or NEG and make sure the first feeling in the feeling list corresponds with this sentiment. If the sentence also includes an event include then on the next line write <event> followed by the event that was described, end this with </event>. The event should be described in the second person and be a complete sentence. "{feeling}".
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
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# Post-process the output to get the sentiment and feelings.
	response = feelings_post_process(model_output)

	# Return a JSON response
	return jsonify(response)


# The ask for thought prompt: Expected output is:
# <question> question </question>.
# Asking the the user for any self-talk/beliefs/thoughts in the
# context of the event. 
# This prompt includes one example.
_ASKING_FOR_THOUGHT_PROMPT = """The following sentence is an activating event identified during the ABC of a CBT session. "{event}" You must now ask the user to identify any thoughts, beliefs or self-talk to help keep them on track with their CBT session. Give your response must start with <question> followed by the question to identify self-talk, beliefs or thoughts. End with </question>. Ask the question in a friendly way.
"""

_DEFAULT_ASK_FOR_THOUGHT = """
When you think about this situation, what's going through your head? Any recurring thoughts or beliefs?"""

def ask_for_thought_post_processing(model_output: str) -> str:
	"""Post processes outputs from the _ASKING_FOR_THOUGHT prompt."""

	question = utils.post_process_tags(model_output, 'question')

	return dict(question=question)

@app.post('/thought')
def ask_for_thought():
	"""Asks user for their thoughts, belief or self-talk."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Create the feelings prompt.
	# The "event" key comes from the http_ask_for_thought widget on the Twilio side.
	prompt = _ASKING_FOR_THOUGHT_PROMPT.format(
		event=message_body['event'])

	# Call to the LLM
	model_output = call_api(
		origin='ask_for_thought',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# Post process the response to get the distortion and question to ask the user.
	response = ask_for_thought_post_processing(model_output)

	return jsonify(response)


_DISTORTION_DETECTION_PROMPT = """
For the following sentence you need to identify the distortions in the users thinking and pose a question to help them realise that distortion. For distortion question pair you must start on a new line with the key <distortion> followed by the distortion, end this with </distortion>. Then on the next line write <question> followed by a question that would help someone identify the distortion, end this with </question>. The question should not directly reference the distortion and should be relevant to the original sentence. "{belief}"
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
	model_output = call_api(
		origin='detect_distortions',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# The model may have recognised several distortions (separated by '\n\n').
	# For now just take one of these.
	# TODO(toni) Use all of the distortions.
	model_output = model_output.split('\n\n')[0]

	# Post process the response to get the distortion and question to ask the user.
	response = distortion_detection_post_processing(model_output)

	return jsonify(response)

_POSITIVE_FEEDBACK_PROMPT = """
For the following sentence, start your response with <response> then write down a sentence, in the 2nd person, praises the user if they have achieve something, otherwise response appropriately in a supportive way. End with </response >. Do not ask any questions. "{positive_event}"
"""

def positive_feedback_post_processing(model_output: str) -> str:
	"""Post processes outputs from the _DISTORTION_DETECTION_PROMPT prompt."""

	response = utils.post_process_tags(model_output, 'response')

	return dict(response=response)

@app.post('/positive_feedback_test')
def positive_feedback_test():
	"""TEST: Responds to users reason for being in a positive mood."""
	response = {
		'response': 'Great work today!',
	}
	# Return a JSON response
	return jsonify(response)


@app.post('/positive_feedback')
def positive_feedback():
	"""Responds to users reason for being in a positive mood."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json

	# Create the feelings prompt.
	# The "belief" key comes from the http_detect_distortions widget on the Twilio side.
	prompt = _POSITIVE_FEEDBACK_PROMPT.format(
		positive_event=message_body['positive_user_event'])

	# Call to the LLM
	# TODO(toni) Call the LLM
	model_output = call_api(
		origin='positive_feedback',
		out_dir=OUT_GPT_DATA_PATH,
		prompt=prompt)

	# Post process the response to get the distortion and question to ask the user.
	response = positive_feedback_post_processing(model_output)

	return jsonify(response)

@app.post('/save_abc_data')
def save_abc_data():
	"""Saves data at the end of the ABC chat."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = str(hash(message_body['user_id']))

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