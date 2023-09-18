"""Functions to recommend which tool to use."""

from flask import jsonify, request
import sys

sys.path.append('..')
import utils

_RECOMMENDER_SYSTEM_PROMPT = """In this coaching session you must recommend on of 5 tools based on how the user is feeling. The tools are described below.

Cheerlead:
This is great for anyone with low confidence or someone who is being too hard on themselves. This tool helps users practice showing the compassion to themselves.

Set Daily Goal:
This is great for helping people get tasks done today. This tool helps users set SMART goals.

Reflect:
The reflection tool is helpful for users who have distortions in their thinking. This tool guides users through the ABC from CBT.

Release and Focus:
This is great for users who feel helpless or lack of control. This tool can help users focus on what's within their control and release what they cannot control.

Daily Gratitude:
This is great for users who are short on time and what to brighten up their day.

The assistant responds with one or two suggestions and a simple explanation. The response should be one sentence long."""


_ASK_USER_HOW_THEY_FEEL = """Please tell me how you are feeling or what you would like help with and I'll do my best to recommend a tool."""

def recommend_tool(request):

	# Get the inputs.
	message_body = request.json
	user_feeling = message_body['user_feeling']

	# Reconstruct the conversation so far.
	messages = [
	{"role": "system", "content": _RECOMMENDER_SYSTEM_PROMPT},
	{"role": "assistant", "content": _ASK_USER_HOW_THEY_FEEL},
	{"role": "user", "content": user_feeling},
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	response = model_output['choices'][0]['message']['content']

	return jsonify(
		response=response
	)

