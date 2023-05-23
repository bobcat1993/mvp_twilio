"""Util. functions."""

import json
import os

def dummy_call_api(
	origin: str,
	out_dir: str,
	model="dummy-model",  # gpt-3.5-turbo
	prompt="Say this is a test",
  max_tokens=7,
  temperature=0,
  ):
	"""Dummy API call.

	Save the response to OUT_DATA_PATH/{origin}-{xid}

	Args:
		origin: The origin of the api call.
		out_dir: The directory to save the response.
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
			"logprobs": 'null',
			"finish_reason": "length"
		  }
		],
		"usage": {
			"prompt_tokens": 5,
			"completion_tokens": 7,
			"total_tokens": 12
		}
	}

	# Save the response.
	# We want to save all responses so that we have a clear record of what's been
	# tried so far.
	json_object = json.dumps(response)
	path = os.path.join(out_dir, 'dummy_responses.json')
	with open(path, "a") as outfile:
		outfile.write(json_object)


	# TODO(toni) Check finish reason! Needs to be "stop" not "length".
	return response