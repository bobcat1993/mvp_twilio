"""Functions to welcome the user."""

from flask import jsonify, request
import sys
import re

sys.path.append('..')
import utils

_QANDA_SYSTEM_PROMPT = """You are an app called BobbyChat with 5 skills you can teach the user, these are listed below. The user will ask you about the skills you have available and you must answer where you can. If you are unsure, say you are unsure and tell the user to contact toni@bobby-chat.com with any questions.

Cheerlead (2mins):
This is great for anyone with low confidence or someone who is being too hard on themselves. This tool helps users practice showing the compassion to themselves.

Set Daily Goal (3mins):
This is great for helping people get tasks done today. This tool helps users set SMART goals.

Reflect (3mins+):
The reflection tool is helpful for users who have distortions in their thinking. This tool guides users through the ABC from CBT.

Release and Focus (2mins):
This is great for users who feel helpless or lack of control. This tool can help users focus on what's within their control and release what they cannot control.

Daily Gratitude (1min):
This is great for users who are short on time and what to brighten up their day.

The assistant gives short responses of one or two sentences. BobbyChat is not a medical device."""


# TODO(toni) Move to utils.py file,
def _remove_questions(text):
	sentences = re.split(r'(?<=[.!?]) +', text)  # Split the text into sentences
	non_question_sentences = [sentence for sentence in sentences if not sentence.endswith("?")]
	result = ' '.join(non_question_sentences)
	return result

# TODO(toni) Add memory.
def qanda_tool(request):
	"""Used to ask Bobby what tools are available."""

	# Get the inputs.
	message_body = request.json
	user_question = message_body['user_question']

	# Reconstruct the conversation so far.
	messages = [
	{"role": "system", "content": _QANDA_SYSTEM_PROMPT},
	{"role": "user", "content": user_question},
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=0.0,  # No stochastic behaviour -- deterministic!
		)

	# Get the response.
	response = model_output['choices'][0]['message']['content']

	# Remove any questions from Bobby.
	response = _remove_questions(response)

	# If there is nothing left after removing the question.
	if not response:
		response = "Sorry, I can't help with that, please contact toni@bobby-chat.com for more details."

	return jsonify(
		response=response
	)

