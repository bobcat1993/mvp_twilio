"""A 7-day Journaling Challenge."""
from datetime import datetime
from flask import Flask, jsonify
import json
from absl import logging
from hashlib import md5
import numpy as np

import sys
sys.path.append('..')
sys.path.append('.')
import utils

# TODO(toni) Move to utils.
def string_hash(string):
	return md5(string.encode()).hexdigest()

def get_JournalingDatum(db):
	class JournalingDatum(db.Model):
		"""Stores the data from the journaling journey flow."""

		id = db.Column(db.Integer, primary_key=True)
		user_event = db.Column(db.String, nullable=True)
		start_time = db.Column(db.DateTime, nullable=True)
		approx_end_time = db.Column(db.DateTime, nullable=True)
		last_user_response = db.Column(db.String, nullable=True)
		user_unsure = db.Column(db.String, nullable=True)
		user_does_not_commit = db.Column(db.String, nullable=True)
		user_feel_after = db.Column(db.String, nullable=True)
		history = db.Column(db.String, nullable=True)
		flow_sid = db.Column(db.String, nullable=True)
		origin = db.Column(db.String, nullable=True)
		user_id = db.Column(db.String, nullable=True)
		error = db.Column(db.String, nullable=True)
		time = db.Column(db.DateTime, nullable=True)

	return JournalingDatum


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
	"""Write down one thing that brings you joy - these can be big or small! What is it about this that means so much to you?""",
	"""What is one thing you do really well, and when is this thing most valuable to you?""",
	"""What does success mean to you?""",
	"""If you had all the time and resources you needed, what activities or hobbies would you pursue?""",
	"""You are doing a great job! How does it feel to read this?""",
	"""Write a short letter of thanks you’ve always wanted to send, but haven’t got round to doing.  This letter could be to someone else, but it could also be to yourself!"""
]

_FOLLOW_UP_EXAMPLE_QUESTIONS = [
"""What was unique about this experience?
Who was with you, and what did it mean to have them there?""",
"""How might you be able make more time for this?""",
"""How did you gain this strength?
How do you use your strength to help others?""",
"""What does society expect success to mean, and how does your version of success fit with this?
What do you find valuable about society’s version of success, and what don’t you find valuable about it?""",
"""Is there a way that you could try or learn this thing now?
  What’s stopping you or holding you back?
  How can you prioritise spending more time doing fun activities?""",
"""Do you believe that you are doing a good job?
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

_DO_YOU_WANT_TO_CONTINUE = [
	'Do you want to continue?',
	'Are you ready for another question?',
	'Do you feel like you\'ve captured your thoughts and feelings for today or would you like to continue?',
	'Is there anything else you\'d like to touch upon before we finish?',
	'Have you reached a good stopping point in your journaling?',
	'Is there a closing reflection or insight you\'d like to add?',
	'Have you expressed what you needed to in your journal?',
	'Is there a final note or sentiment you\'d like to record before we wrap up?',
	'Are you content with the progress you\'ve made in your journaling today or would you like to keep going?']

# Check if the user wants to stop every _ASK_TO_CONTINUE_EVERY_N messages. This MUST BE EVEN.
_ASK_TO_CONTINUE_EVERY_N = 6


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

	# Always an odd number of messages hence looking at == 1, rather than 0.
	logging.info('Number of message: %s', len(messages))
	logging.info('Eval: %s', (len(messages) > _ASK_TO_CONTINUE_EVERY_N) and (len(messages) % _ASK_TO_CONTINUE_EVERY_N == 1))

	if (len(messages) > _ASK_TO_CONTINUE_EVERY_N) and (len(messages) % _ASK_TO_CONTINUE_EVERY_N == 1):
		# Ask the user (in a nice way) if they are done with journaling.
		question = np.random.choice(_DO_YOU_WANT_TO_CONTINUE)
	else:
		# Otherwise continue asking questions.

		model_output = utils.chat_completion(
			model="gpt-3.5-turbo-0613",
			messages=messages,
			max_tokens=1024,
			temperature=1.0,
			)

		question = model_output['choices'][0]['message']['content']
	
	history.append({"role": "assistant", "content": question})

	# If the model does not ask a question, end the session.
	if '?' in question:
		is_done = False
	else:
		is_done = True

	# Note that the last output from this loop is a question from the 
	# model, not a user response.
	return jsonify(
		question=question,
		messages=messages,
		history=json.dumps(history),
		is_done=is_done,
		time=datetime.now())

def save_data(request, db, JournalingDatum):
	"""Saves data at the end of a journaling session."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
		now = datetime.now()
		message_body['time'] = now

		# Dump the history (into dicts).
		history = message_body['history']
		message_body['history'] = json.dumps(history)

		datum = JournalingDatum(**message_body)
		db.session.add(datum)
		db.session.commit()
		return jsonify({'message': f'Flow data saved.'}), 200

	except Exception as e:
		logging.error('error: %s', str(e))
		return jsonify({'error': str(e)}), 400
