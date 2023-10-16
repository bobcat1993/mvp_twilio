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

_JOURNALING_TOPICS = {
	"Time Management" : [
		["Let's do a daily time audit. Describe how you spent your time today.", "What activities were the most time-consuming, and were they productive or time-wasting?", "How could you have used your time more efficiently?"],
		["Let's consider prioritisation. Write about your current methods for setting priorities and organizing tasks.", "Are there specific strategies you use to determine what's most important?", "How effective are these strategies?"],
		["Let's take a look consider time-wasting. What habits or behaviours consistently waste your time?", "What steps can you take to minimize or eliminate them from your daily routine?"],
		["Imagine you have a completely free day to plan and organize as you see fit. Describe your ideal daily schedule, including work, personal time, and self-care.", "What changes can you make to your current schedule to align it more closely with this ideal?"],
		["Let's think about time-management tool. Write about the tools and techniques you use to manage your time, such as calendars, to-do lists, or time management apps.","Are there new tools or strategies you're considering implementing to enhance your time management?"],
		["Let's explore your approach to setting deadlines for projects and tasks. Are you realistic in your expectations, or do you often overcommit and feel overwhelmed?", "How can you become better at estimating time requirements?", "Do you feel comfortable saying no to things?"],
		["Write down your time management goals for the upcoming week.", "What specific steps can you take to improve your time management in the areas where you struggle the most?"]
	],
	"Work-Life Balance" : [
		["Let's Begin by assessing your current work-life balance. How do you feel about the balance between your work life and personal life?", "Are there areas where you feel you're doing well?" "Where do you struggle?"],
		["Let's explore your priorities. Write about your top priorities in life, both in your career and personal life.", "Are your current commitments and actions aligned with these priorities, or do you need to make adjustments?"],
		["Let's explore your routine, Describe your typical daily and weekly routines.", "How do you allocate your time between work, family, friends, hobbies, and self-care?", "Are there changes you'd like to make to achieve a more balanced routine?"],
		["Let's reflect on your ability to set boundaries and say \"no\" when necessary. Do you often overcommit or find it challenging to decline additional work or personal obligations?", "Where would you like to set more boundaries?", "Who do you need to talk to make your boundaries more clear?"],
		["Let's talk about your self-care practices and relaxation techniques. What activities help you unwind, recharge, and reduce stress?", "Are there ways to incorporate more self-care into your daily or weekly routine?"],
		["Let's consider the idea of work-life integration. Are there examples where boundaries between work and personal life are more fluid?", "How do you feel about this boundary?", "Is there anything you would like to change about this boundary?"],
		["Set weekly balance goals for yourself. What specific actions or changes can you implement in the upcoming week to achieve a better work-life balance?", "How are you going to implement these actions or changes?"]
	],
	"Communication Skills": [
		["Let's begin by assessing your current communication skills. What do you think are your strengths and weaknesses in communication?", "Please give examples of situations where your strengths in communication were evident?", "Are there specific areas or situations where you feel your communication needs improvement?"],
		["Let's consider at your listening skills. Do you find it easy to listen to other people?", "Can you think of a recent conversation where better listening (by yourself or someone you were talking to) could have improved the outcome?", "What habits or practices can you adopt to actively engage in conversations?"],
		["Describe a recent conflict and how you handled it.","Is there something that you wish you had done differently?", "How do you think this would have affected the outcome?", "What specific steps can you take to handle similar conflicts more effectively in the future?"],
		["Do you ever struggle with expressing your needs or respecting others' boundaries?", "Can you recall a situation where you had difficulty expressing your needs or setting boundaries?", "Try constructing a sentence of the form: 'I feel [emotion] when [event] because [reason]. I would like [change].' For example, I feel upset when you talk over me because I find it disrespectful. I would like you to wait for me to finish speaking.?"],
		["Let's consider your tone of voice. What tone of voice did you last communicate with?", "Do you think this tone was appropriate or would you have changed it?", "Do you think this tone of voice helped or hindered the conversation?"],
		["Let's talk about empathy. Can you think of a recent situation where understanding someone else's perspective was challenging?", "What made their perspective difficult to understand?", "Have you experienced a similar situation to them before?"],
		["Thinking about the next few days ahead of you, what specific communication areas would you like to work on, and what steps can you take to improve?", "What are your short-term and long-term goals for improving your communication skills?", "What small improvement will you start with today?"]
	],
	"Setting Realistic Goals": [
		["Let's identify your goals. What are your current goals or aspirations?", "Why are these goals important to you?"],
		["Write down one of your goals.", "Is your goal a S.M.A.R.T. (Specific, Measurable, Achievable, Relevant, Time-bound) goal?", "How can you make your goal more specific, measurable, achievable, relevant, or time-bound?"],
		["Let's talk about prioritization. Rank your goals in order of importance to you.",  "How can you allocate your time and resources effectively to work toward your top priorities?"],
		["Write down one of your goals (it can be one from a previous session or a new one). What obstacles or challenges do you foresee in achieving your goals?", "How can you address or overcome these obstacles?", "Is there anyone that can help you?"],
		["Let's look at breaking  down one of your larger goals into smaller, actionable steps. Which of your goals currently seems too large to manage in one go?", "What are some intermediate steps you can take to achieving this goal? I'm here to help you break it down if needed.", "Do you feel that this breakdown is more manageable and achievable?"],
		["Write down one of your goals (it can be one from a previous session or a new one). How do you plan to track your progress toward this goal?", "What metrics or markers will you use to measure your success along the way?"],
		["Write down one of your goals (it can be one from a previous session or a new one). What motivates you to work toward this goal?", "How can you stay motivated when faced with setbacks or difficulties on your path to achievement?", "Is there anyone or anything that depends on you achieving this goal?"]
	],

	"Workplace Challenges" : [
		["What is the most significant challenge you're currently facing in your work at the moment?", "Why do you feel that this challenge is important to address, and how does it impact your overall well-being?", "Have you discussed this challenge with anyone else?"],
		["Please recall a significant challenge you are facing at work (it can be one from a previous session). What potential solutions or strategies can you think of to overcome this challenge?", "Are there resources or support systems that can help you address this challenge effectively?", "Which solution or strategy do you believe is the most promising?", "How can you break down your chosen solution into actionable steps?"],
		["Please recall a significant challenge you are facing at work (it can be one from a previous session). What obstacles or barriers do you anticipate as you work to resolve this challenge?", "Have you faced similar obstacles in the past? How did you handle them?", "Who can you reach out to for guidance or support in tackling these obstacles?"],
		["Please recall a significant challenge you are facing at work (it can be one from a previous session). What lessons or insights have you gained from this challenge so far?", "How can you use this experience to foster personal or professional growth?", "What skills or knowledge can you acquire through addressing this challenge?", "In what ways can you apply the lessons learned to future situations?"],
		["Please recall a significant challenge you are facing at work (it can be one from a previous session). Are there milestones you can set to measure your progress?", "How often will you review you progress?"],
		["Please recall a significant challenge you are facing at work (it can be one from a previous session). You don't have to face all challenges alone. Who can you turn to for support or guidance as you work through this challenge?", "How can you effectively communicate your needs to those who can assist you?", "What types of support are you most in need of right now?", "How can you express your gratitude to those who offer help or guidance?"],
		["Please recall a significant challenge you are facing at work (it can be one from a previous session). How have you been coping with the stress or pressure caused by this challenge?", "What self-care practices help you recharge during challenging times? It could be as simple as having a coffee with a friend.", "What motivates you to overcome this challenge?"]
	],

	"Imposter Syndrome" : [
		["Let's begin with recognizing imposter feelings. Tell me about a recent situation where you felt like an imposter.", "What triggered these feelings, and how did they manifest?", "Are there recurring patterns or triggers for your imposter feelings?", "What emotions or thoughts accompany these feelings?"],
		["It's really important acknowledge your achievements! List your any accomplishments, qualifications, and experiences. How have these achievements contributed to your expertise or competence?", "Are you downplaying or discounting any of your achievements?", "Is there anything that can use to remind yourself of your capabilities and accomplishments?"],
		["Have you received any external validation of your skills? Did someone say 'good job' or have you completed a qualification?", "Do you tend to undervalue external validation or view it as temporary?", "How might you use external validation as a source of motivation and reassurance?"],
		["Let's challenge any negative self-talk. Write down one negative self-talk or self-criticism you have of yourself.", "What evidence contradicts the negative self-talk?"],
		["Let's think about defining some realistic expectations for yourself. Can you differentiate between striving for excellence and seeking perfection?", "Are your expectations aligned with your current goals and abilities?", "How can you reframe your expectations to reduce imposter feelings?"],
		["Let's think about your support network. Did you know that many of the people you many consider mentor or role models are likely to also have experienced imposter syndrome. Who might you turn to for support, mentorship, or advice?", "What specific questions or concerns can you bring to your support network?"],
		["Document your progress and self-reflection on your journey to overcome imposter syndrome. How have your efforts to combat imposter feelings evolved over time?", "Have you celebrated small wins and moments of self-assurance?", "What strategies or practices have been most effective in diminishing imposter syndrome?"]
	],

	# Easy one (gets harder towards the end).
	"Prioritizing Self-Care":  [
		["I want to understand, what does self-care mean to you, and why do you think it's important?", "What aspects of self-care are most challenging for you?", "How might practising self-care positively impact your life?"],
		["Describe a self-care activity you engaged in today, no matter how small. How did it make you feel, and why did you choose this activity?", "What time of day did you do this activity?", "Could you imagine making this a regular part of your self-care routine?"],
		["Finding time for self-care can be a challenge. What tends to get in the way of your self-care?", "Are there patterns or recurring barriers you notice in your self-care efforts?", "Is there a way for you to address or overcome these obstacles?"],
		["Let's make a Self-Care Wish List! Create a list of self-care activities you'd like to explore or prioritize in the future.", "What's stopping you from trying these self-care activities?", "Can you set a goal to try one of the activities on your list?"],
		["How does it feel after engaging in self-care. Do you notice any changes in your mood, stress levels, or overall well-being?", "How can you become more aware of your emotional responses to self-care?", "How can these positive emotions motivate you to continue prioritizing self-care?"],
		["Let's talk about boundaries! Are you comfortable saying \"no\" to additional commitments when you need self-care time?", "Recall the last time you wanted to say no to additional commitments, how did it go?", "Try constructing a sentence of the form: 'I feel [emotion] when [event] because [reason]. I would like [change].' I'm here to help if you need it."
		],
		["Time to write a Self-Care Commitment outlining your intention to prioritize self-care. What will you do to make self-care a regular part of your life?", "How will you hold yourself accountable to this commitment?", "Can you create a self-care routine or schedule to help you stay on track?"
		]
	]

}

def get_number_of_days_journaled(user_number, db, JournalingDatum):
	"""Get the number of journal entries for the user."""

	# Hash the user number to match it in the data frame.
	user_id = string_hash(user_number)

	# Getting the sessions where the user has journaled and written something down. If the user gets a prompt and does not write something it will not count as a day.
	user_sessions = db.session.query(JournalingDatum).filter(JournalingDatum.user_id == user_id).all()

	# The total number of days journaled.
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
