"""A 7-day Journaling Challenge."""
from datetime import datetime
from flask import Flask, jsonify
import json

import sys
sys.path.append('..')
sys.path.append('.')
import utils


def _days_since_start():
	# Replace 'YYYY-MM-DD' with your desired start date in the format 'YYYY-MM-DD'
	start_date_str = '2023-10-09'

	# Convert the start date string to a datetime object
	start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

	# Get the current date
	current_date = datetime.today()

	# Compute the difference between the current date and the start date
	days_difference = (current_date - start_date).days

	# Don't allow negative days.
	days_difference = max(0, days_difference)

	return days_difference

_JOURNAL_PROMPTS = [
	"""Relive a magical moment! Complete this sentence:  “One of the best experiences of my life was…”. Explain the experience and why you are grateful for it.""",
	"""Write down 5 things that bring you joy - these can be big or small! What is it about these things that means so much to you?""",
	"""What three things do you do really well, and when are these things most valuable to you?""",
	"""What does success mean to you?""",
	"""If you had all the time and resources you needed, what activities or hobbies would you pursue?""",
	"""You are doing a great job! How does it feel to read this?""",
	"""Write a short letter of thanks you’ve always wanted to send, but haven’t got round to doing.  This letter could be to someone else, but it could also be to yourself!"""
]

_FOLLOW_UP_EXAMPLE_QUESTIONS = [
"""What was unique about this experience?
Who was with you, and what did it mean to have them there?""",
"""How might you be able to have you have more of these things in your life?""",
"""When are these strengths most useful?
How do you use your strengths to help others?""",
"""What does society expect success to mean, and how does your version of success fit with this?
What do you find valuable about society’s version of success, and what don’t you find valuable about it?""",
"""Is there a way that you could try or learn this thing now?
  What’s stopping you or holding you back?
  How can you prioritise spending more time doing fun activities?""",
"""Do you believe it?
When was the last time you said this or heard this?""",
"""What are you thankful for and why?"""
]

_FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT = """The assistant is helping the user journal. The assistant has given a prompt and will ask follow up question to help the user explore their thoughts. Questions should be short, friendly and thoughtful.

Here are some example follow up questions, only ask one question at a time:
{example_questions}"""

_PROMPT_URL = "https://storage.googleapis.com/bobby-chat-journaling/day{day_no}.png"


def get_journal_prompt(request):
	"""Give the journaling prompt of the day"""

	# Get the day number/ index.
	day_index = _days_since_start()

	# Get the prompt and follow up questions based on the day.
	# Default to day one if the challenge has not started.
	idx = day_index % len(_JOURNAL_PROMPTS)
	prompt = _JOURNAL_PROMPTS[idx]
	follow_up_questions = _FOLLOW_UP_EXAMPLE_QUESTIONS[idx]
	
	return jsonify(
		day=str(day_index + 1),
		idx=idx,
		prompt=prompt,
		follow_up_questions=follow_up_questions,
		prompt_url=_PROMPT_URL.format(day_no=day_index + 1),
		time=datetime.now()
	)


def ask_follow_up_questions_loop(request):
	"""Asks user for their thoughts, belief or self-talk."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json
	user_event = message_body['user_event']
	prompt = message_body['prompt']
	follow_up_questions = message_body['follow_up_questions']
	history = message_body['history']
	last_user_response = message_body['last_user_response']

	if last_user_response:
		history.append({"role": "user", "content": last_user_response})

	# Generate a question to ask the user for their thoughts about an event.
	messages= [
		{"role": "system", "content": _FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT.format(example_questions=follow_up_questions)},
		{"role": "assistant", "content": prompt},
		{"role": "user", "content": user_event},
		*history
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		)

	question = model_output['choices'][0]['message']['content']
	history.append({"role": "assistant", "content": question})

	# For now keep going until there is a time-out.
	is_done = False

	# Note that the last output from this loop is a question from the 
	# model, not a user response.
	return jsonify(
		question=question,
		messages=messages,
		history=json.dumps(history),
		is_done=is_done,
		time=datetime.now())
