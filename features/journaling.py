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
		topic = db.Column(db.String, nullable=True)
		topic_idx = db.Column(db.Integer, nullable=True)

	return JournalingDatum

_FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT = """The friendly assistant is helping the user journal. The assistant has given a prompt and will ask follow up questions to help the user explore their thoughts. Questions should be short, friendly and thoughtful.

If the user asks for help, help them by simplifying the question or posing it in a different way.

The assistant always asks one question at a time."""

_JOURNALING_TOPICS = {

	"Time Management" : [
		["Let's do a daily time audit. Describe how you spent your time today. What activities were the most time-consuming, and were they productive or time-wasting?", "How could you have used your time more efficiently?"],
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
	],

	# Student
	"Social Media": [
		["Are you the same person on social media as you are in real life?", "What are the main differences?"],
		["What would you teach the world in an online video?", "Who would your audience be?"],
		["How do you archive your life?", "Why do you choose this method to archive your life?"],
		["Have you ever posted, emailed or texted something you wish you could take back?", "Why did you wish you could take it back?", "What would you like to have done differently?"],
		["How would you feel if an employer were to look at your posts?", "Is there anything you would rather an employer not see?"],
		["Do you worry we are filming too much?", "How does filming affect your enjoyment of life events?"],
		["What is something positive you have seen on social media?", "How did it make you feel?", "Did it inspire you with any ideas of your own?"]
	],

	# Student
	"Choosing a Job": [
		["What careers are you most curious about?", "Why do these careers interest you?"],
		["What are your long time interests or passions?", "What is it that you enjoy most about you passion/interest?", "Could you imagine turning your passion/interest into a career?"],
		["Do you think that you will have a career that you love?", "What would make you love your career?"],
		["What investments are you willing to make to get your dream career", "What steps have you already taken?", "Which of these investments might be challenging?"],
		["What would you choose to you if you had unlimited free time and no restrictions?", "Do these things relate to your career goals?", "Are you able to make time for some of these things?"],
		["Where do you want to see yourself in 10 years?", "What choices that you make today will affect you 10 years from now?", "How do other people's expectations, influence your answer?"],
		["What is important to you now that will still be important to you in 5 years time?", "Why is it important to you?"]
	],

	# Student
	"Parental Expectations": [
		["How are you similar or dissimilar to your parents?", "What do you think of these differences?", "Do you respect each other's differences?"],
		["Will you follow in your parents footsteps or carve your own path?", "Who will set your path?", "Do you feel any pressures?"],
		["How much freedom have your parents given you?", "How has that affected your life choices up to this point?", "How will it affect future decisions?"],
		["What is your role within your family?", "Why do you play that role?", "What do you like most about that role?"],
		["What does family mean to you?", "How has it's meaning changed since you were young?"],
		["What is your favourite family memory?", "What about that memory is special?", "When was the last time you made a family memory like this?"],
		["Did you pick up any hobbies from your family?", "When was the list time you did that?", "Why do you enjoy it?"]
	],

	# Slightly studenty.
	"Friendships": [
		["Do you feel like you spend enough time with other people?", "Is there someone you would like to spend more/less time with?", "Do you have enough time?"],
		["How often do you spend one-on-one time with your closest friends?", "What do you enjoy most about that time?"],
		["Do you prefer to make new friends online or in person?", "Where do you typically make new friends?"],
		["How have you helped a friend in a time of need?", "How did this affect your relationship?"],
		["How do you feel about introducing friends from different parts of your life?", "Have you tried?", "How do you think it would go?"],
		["Have you had a friendship come to an end?", "How did you handle it?", "Did you learn anything about yourself?"],
		["What makes you feel left out?", "Do you think people do this intensionally?", "How might you ask to be included?"]
	],

	# This one is somewhat accessible.
	"Growth Mindset":
	[
		["Do you have any limiting self-beliefs? For example, do you ever say 'I can't'?", "What is your strongest limiting self-belief?", "Can you think of any evidence that is counter to this belief?"],
		["What does your inner voice say to you?", "Is it mostly positive or negative?", "How do you react to your inner voice?"],
		["Are you living your life in the past, the present moment, or in the future?", "What stories do you tell yourself about your past?", "What can you take away from it?", "What can you learn from your past to serve your today in the moment?"],
		["What are your beliefs and how do they help you get through life's challenges?", "Do your beliefs and values align or contradict?"],
		["Are you afraid of change, being challenged, or failing?", "What's the worst that can happen?", "What opportunities might you miss out on if you give into fear?"],
		["What are some goals today, long-term goals, or life goals you need to get to where you want to be?", "What steps are you already taking towards these goals?", "What does the path to your goal look like?"],
		["Has something previously got in the way of your dreams? How did you grow to overcome it?", "What did you learn?", "How can that experience inspire you to work through challenges?"]
	],

	# This one is reasonable accessible.
	"Having a Bad Day": [
		["What happened today and what is bothering you?", "What are you thinking and feeling?"],
		["What is something helpful you might tell someone whose having a similarly bad day?", "How does it feel to say those things to yourself?"],
		["What negative thoughts can up for you today?", "Are these thoughts helpful?", "What might be a more helpful re-framing of this thought."],
		["What did you feel like you had not control over today?", "Was there anything that you did feel you had control over?", "Can you begin to accept what was outside of your control?"],
		["Remember the last time you had a bad day. When helped you get through it?", "Why did that work?"],
		["What happened today and what can you learn from this experience?", "How do these experiences make you stronger?"],
		["Is there something kind you can do for yourself when you are feeling down? Write them down.", "Would you do any of them with a friend?"],
	],

	# This one is good and reasonable accessible.
	"Self-Reflection":[
		["What opportunities might you have soon that put you outside of your comfort zone?", "How do they make you feel?", "What might you do to encourage your self to try them?"],
		["If you could, what would you tell your teenage self that would help you now?", "How would that help you?"],
		["What would a close friend say you need to work on?", "What steps do you need to take to begin working on this?"],
		["If you were having a perfect day what would you be feeling and thinking", "How do your thoughts and feeling influence your day?"],
		["Are there any boundaries you feel you need to set between yourself and others?", "What is the first step to setting these boundaries?", "How comfortable are you asserting your boundaries?"],
		["What would you like to say 'no' to? Make a list.", "Can you say 'no' to any of these things?", "Can you gain some control by deciding when you do some of these things?"],
		["If you were guaranteed that today was the perfect time to do something, what would you do?", "How would doing that make you feel?", "Would you see yourself differently?"]
	],

	# This one is good and reasonable accessible.
	"Self-Care": [
		["What are a few small things you can do for yourself today?", "How can you make time for them?"],
		["Think of the last kind thing you did for yourself. What were the benefits?", "How long ago was this?", "Is there a way to more regularly include this in your schedule?"],
		["What would a perfect evening look like to you?", "What small change might you make to your evenings to make them more similar to your perfect evening?"],
		["When you are swamped, how can you find 10 mins for yourself?", "What can you do in those 10 mins?"],
		["What small thing can you do to prioritize your physical health?", "How can you implement this?"],
		["If you were to make a self-care box, what would you put in it?", "How would you use it?"],
		["How do you advocate for yourself?", "Who would you advocate to?", "What would you say?"]
	]

}

_CURRENT_OPTIONS = [
	'Self-Care', 'Self-Reflection', 'Having a Bad Day', 'Growth Mindset', 'Friendships', 'Choosing a Job', 'Social Media', 'Prioritizing Self-Care', 'Imposter Syndrome', 'Workplace Challenges', 'Setting Realistic Goals', 'Communication Skills', 'Work-Life Balance', 'Time Management'
	]

def get_most_recent_topic_and_topic_idx(user_number, db, JournalingDatum):
	"""Get the topic and the topic_idx"""

	# Hash the user number to match it in the data frame.
	user_id = string_hash(user_number)

	# Getting the sessions where the user has journaled and written something down. If the user gets a prompt and does not write something it will not count as a day.
	user_session = db.session.query(JournalingDatum).filter(JournalingDatum.user_id == user_id).all()

	if user_session:
		user_session = user_session[-1]
		return dict(topic_idx=user_session.topic_idx, topic=user_session.topic)
	else:
		return dict(topic_idx=None, topic=None)


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
	"""Give the journaling prompt if there is one."""

	message_body = request.json
	user_number = message_body['user_number']

	# Get the day number/ index.
	topic_info = get_most_recent_topic_and_topic_idx(user_number, db, JournalingDatum)

	topic = topic_info['topic']
	topic_idx = topic_info['topic_idx']

	print('topic:', topic)
	print('topic_idx:', topic_idx)

	if topic_idx is None:
		# The user has not topic selected.
		message = 'Hi, I\'m excited that you have chosen to start journaling with me.'
		return jsonify(
			topic=None,
			topic_idx=None,
			prompt=None,
			follow_up_questions=None,
			time=datetime.now(),
			message=message,
			select_new_topic=True)

	# Get all prompts in that topic.
	prompt_list = _JOURNALING_TOPICS[topic]
	print('len(prompt_list):', len(prompt_list))
	# If the topic_idx is within the range, get the prompt.
	if len(prompt_list) > topic_idx + 1:
		prompt = prompt_list[topic_idx + 1]
		message = f'Hi, great to see you again! You have made your way to session {topic_idx + 2} out of {len(prompt_list)} in the {topic} prompt series.'
		return jsonify(
			topic=topic,
			topic_idx=topic_idx + 1, # Progress the topic_idx by one.
			prompt=prompt[0],
			follow_up_questions='\n'.join(prompt[1:]),
			message=message,
			time=datetime.now(),
			select_new_topic=False)
	else:
		# The topic_idx must be out of range.
		message = f'Hi, glad you\'re back for more! In the last session you reached the end of the {topic} prompt series. Time to select a new series.'
		return jsonify(
			topic=None,
			topic_idx=None,
			prompt=None,
			follow_up_questions=None,
			time=datetime.now(),
			message=message,
			select_new_topic=True)

# TODO(toni): Use f-string of _CURRENT_OPTIONS for the options.
_ASK_USER_FOR_TOPIC_SYSTEM_PROMPT = """
You are Bobby, a well-being assistant, helping the user journal.

You can help the user journal on the following topics:

'Self-Care', 'Self-Reflection', 'Having a Bad Day', 'Growth Mindset', 'Friendships', 'Choosing a Job', 'Social Media', 'Prioritising Self-Care', 'Imposter Syndrome', 'Workplace Challenges', 'Setting Realistic Goals', 'Communication Skills', 'Work-Life Balance', 'Time Management'.

Ask the user one question at a time to pick a topic most relevant for them.

Once they pick a topic respond with "USER CHOSEN" followed by the chosen topic."""

_BOT_ASKS_FOR_TOPIC = """Think about your day or week so far. Is there a particular experience or feeling that has been on your mind, something you'd like to explore and understand better through journaling?"""

def ask_user_for_journaling_topic_loop(request):
	"""Helps the user choose a topic to journal about."""

	# Retrieve data from the request sent by Twilio
	message_body = request.json
	user_topic_intro = message_body['user_topic_intro']
	history = message_body['history']
	last_user_response = message_body['last_user_response']

	prompt = None
	follow_up_questions = None
	topic = None
	topic_idx = None

	if last_user_response:
		history.append({"role": "user", "content": last_user_response})

	# Generate a question to ask the user for their thoughts about an event.
	messages= [
		{"role": "system", "content": _ASK_USER_FOR_TOPIC_SYSTEM_PROMPT},
		{"role": "assistant", "content": _BOT_ASKS_FOR_TOPIC},
		{"role": "user", "content": user_topic_intro},
		*history
	]

	model_output = utils.chat_completion(
		model="gpt-3.5-turbo-0613",
		messages=messages,
		max_tokens=1024,
		temperature=1.0,
		top_p=1,
		)

	question = model_output['choices'][0]['message']['content']
	
	history.append({"role": "assistant", "content": question})

	if 'USER CHOSEN' in question:
		is_done = True
		for opt in _CURRENT_OPTIONS:
			if opt.lower() in question.lower():
				topic = opt
	else:
		is_done = False

	if is_done:
		if not topic:
			# Use the Self-Reflection topic as default.
			topic = 'Self-Reflection'
		
		prompt_list = _JOURNALING_TOPICS[topic][0]
		prompt = prompt_list[0]
		follow_up_questions = '\n'.join(prompt_list[1:])
		topic_idx = 0  # Start from zero.


	# Note that the last output from this loop is a question from the 
	# model, not a user response.
	return jsonify(
		question=question,
		messages=messages,
		history=json.dumps(history),
		is_done=is_done,
		topic=topic,
		topic_idx=topic_idx,
		prompt=prompt,
		follow_up_questions=follow_up_questions,
		time=datetime.now())

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
		{"role": "system", "content": _FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT},
		{"role": "assistant", "content": f'{prompt}\nLet me know if you are not sure.'},
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
			top_p=1,
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
