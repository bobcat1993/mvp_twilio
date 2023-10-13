"""Permanent Journaling Feature."""
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
"What's one thing that made you smile today?",
"Tell me about the weather outside and how it's affecting your mood.",
"Tell me about something you're looking forward to today.",
"What's your favourite meal or snack from today, and why?:",
"Document one small act of kindness you performed or witnessed today.",
"Reflect on a recent conversation you had and how it made you feel.",
"Share a short gratitude list for the people you interacted with today in person or virtually.",
"What's one thing you achieved or completed today, no matter how small?",
"Tell me about something you'd like to do for yourself this evening.",
"What's one thing you learned today that you didn't know yesterday?",
"Tell me about a challenge you faced today and how you managed it.",
"Tell me about the most interesting or inspiring thing you saw today.",
"Tell me about a small goal or intention for tomorrow.",
"What was the most delicious thing you tasted today? Describe it to me.",
"Where did you spend most of your time today? Describe it to me.",
"Reflect on something that you read today. What did you take away from it?",
"Write about a moment of joy or excitement from your day.",
"Tell me about someone you interacted with today (it can be virtually) and how they made you feel.",
"Tell me about an aspiration that crossed your mind today.",
"Share a moment when you felt proud of yourself today.",
"What's one simple thing you can do to improve your day right now?",
"Sum up your day in one word. Why did you choose that word?",
"Share one thing on your to do list?",
"What thought is top of mind today?",
"What challenge did you face today and how did you deal with it?",
"Tell me about a conversation you had today that left an impression on you.",
"What was the most unexpected thing that happened to you today?  Tell me about it.",
"Reflect on your current goals. Have they changed or evolved recently?",
"What's been on your mind a lot lately?",
"Tell me about your current daily routine and one adjustment you would like to make.",
"Tell me about a recent dream you had and any symbolism it may hold.",
"When you think about current relationships, both with friends and family, what comes to mind?",
"Please share with me a habit you'd like to cultivate or a bad habit you'd like to break.",
"Describe someone who's supported or influenced you today, directly or indirectly.",
"Tell me about something you did today that took you out of your comfort zone.",
"Tell me about a goal or project you're working on and your progress so far.",
"Share your thoughts on a news story or event that caught your attention today.",
"Tell me about your plans for the next few days and how they make you feel.",
"What is your favourite season? How does it affect your mood and outlook?",
"What did you accomplish today? It can be anything small or large.",
"Tell me about a challenge you'd like to tackle in the next few days.",
"Tell me about a personal ritual or routine that brings you comfort. It could be as simple as making a morning coffee.",
"Tell me about one thing that you're proud of in your life right now. Don’t be afraid to recognise your achievements.",
"Please share with me any feeling or emotion that you're experiencing at this moment.",
"Tell me about your day so far. Is there anything you would have liked to do differently?"
]

_FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT = """The assistant is helping the user journal. The assistant has given a prompt and will ask follow up question to help the user explore their thoughts. Questions should be short, friendly and thoughtful.

Only ask one question at a time."""

def get_number_of_days_journaled(user_number, db, JournalingDatum):
	"""Get the number of journal entries for the user."""

	# Hash the user number to match it in the data frame.
	user_id = string_hash(user_number)

	# Getting the sessions where the user has journaled and written something down. If the user gets a prompt and does not write something it will not count as a day.
	user_sessions = db.session.query(JournalingDatum).filter(JournalingDatum.user_id == user_id).all()

	# The total number of days journaled.
	print(user_sessions)
	number_of_days_journaled = len(user_sessions)

	return number_of_days_journaled


def get_journal_prompt(request, db, JournalingDatum):
	"""Give the journaling prompt of the day"""

	message_body = request.json
	user_number = message_body['user_number']

	# Get the day number/ index.
	day_index = get_number_of_days_journaled(user_number, db, JournalingDatum) - 1

	# Get the prompt and follow up questions based on the day.
	# Default to day one if the challenge has not started.
	idx = day_index % len(_JOURNAL_PROMPTS)
	prompt = _JOURNAL_PROMPTS[idx]
	
	return jsonify(
		day=str(day_index + 1),
		idx=idx,
		prompt=prompt,
		time=datetime.now()
	)

_DO_YOU_WANT_TO_CONTINUE = [
	'Do you want to continue?',
	'Are you ready for another question?',
	'Do you feel like you\'ve captured your thoughts and feelings for today or would you like to continue?',
	'Is there anything else you\'d like to touch upon before we finish?',
	'Have you reached a good stopping point in your journaling?',
	'Have you expressed what you needed to in your journal?',
	'Is there a final note or sentiment you\'d like to record before we wrap up?',
	'Are you content with the progress you\'ve made in your journaling today or would you like to keep going?']

# Check if the user wants to stop every _ASK_TO_CONTINUE_EVERY_N messages. This MUST BE EVEN.
_ASK_TO_CONTINUE_EVERY_N = 8


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
