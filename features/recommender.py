"""Functions to recommend which tool to use."""

from flask import jsonify, request
import sys

sys.path.append('..')
import utils

_RECOMMENDER_SYSTEM_PROMPT = """In this coaching session you must recommend one of three tools based on how the user is feeling. The tools are described below.

Reflect:
The reflection tool is helpful for users who have distortions in their thinking. This tool guides users through the ABC from CBT.

Release and Focus:
This is great for users who feel helpless or lack of control. This tool can help users focus on what's within their control and release what they cannot control.

Journaling:
This tool is great for almost anything. Users can choose for a wide variety of topics and if they get stuck they can ask Bobby for help along the way. Journaling can help the user with self-reflection, if they are having a bad day, building a growth mind-set, prioritising self-care, managing imposter syndrome, workplace challenges, setting realising goals, improving communication skills, time management and work-life balance.

The assistant must suggest one or two tools and give a simple, friendly explanation that refers back to the user's feeling. The response should be one sentence long."""


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

