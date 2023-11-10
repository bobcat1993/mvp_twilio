import unittest
import app as my_app
from app import app
from parameterized import parameterized
from abc_types import Sentiment
import logging
from freezegun import freeze_time
from datetime import date, timedelta

# See all the logs.
app.logger.setLevel(logging.INFO)

class TestApp(unittest.TestCase):

	def setUp(self):
		app.config['TESTING'] = True
		app.config['DEBUG'] = True 
		self.app = app.test_client()

	# @parameterized.expand(
	# 	[
	# 	(
	# 		'23:30:12',
	# 		'I notice you are up late. How are you feeling?'
	# 	),
	# 	(
	# 		'03:22:12',
	# 		'It seems early. How are you feeling?'
	# 	),
	# 	(
	# 		'10:00:14',
	# 		'Let\'s start. How you are feeling this morning?'
	# 	),
	# 	(
	# 		'14:23:23',
	# 		'Let\'s begin. How are you feeling this afternoon?'
	# 	),
	# 	(
	# 		'18:22:30',
	# 		'Let\'s start. How have you been feeling this evening?'
	# 	),
	# 	])
	# def test_user_feeling(
	# 	self,
	# 	time: str,
	# 	target_response: str):

	# 	with freeze_time(time):
	# 		response = self.app.post('/user_feeling')

	# 	# Assert the response status code
	# 	self.assertEqual(response.status_code, 200)

	# 	# Assert the response status code
	# 	response_data = response.get_json()
	# 	self.assertEqual(response_data['response'], target_response)

	# @parameterized.expand(
	# 	[
	# 	('I\'m good, thanks.', Sentiment.POS.value),
	# 	# Feeling tired currently seen by the model as neutral.
	# 	# ('Feeling very tired today.', Sentiment.NEG.value),
	# 	('My car broke down, and I\'m feeling frustrated and stressed.',
	# 		Sentiment.NEG.value),
	# 	('I\'m not sure', Sentiment.NEUTRAL.value),
	# 	('I had a really fun time with my friends', Sentiment.POS.value),
	# 	('I had so much fun, sad it\'s over', Sentiment.POS.value),
	# 	('I\'m not sure.', Sentiment.NEUTRAL.value)
	# 	])
	# def test_detect_sentiment(
	# 	self,
	# 	user_feeling: str,
	# 	target_sentiment: str):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {'feeling': user_feeling}

	# 	# Send a POST request to the endpoint with the sample payload
	# 	response = self.app.post('/detect_sentiment', json=payload)
	# 	app.logger.info('response %s', response)

	# 	# Assert the response status code
	# 	self.assertEqual(response.status_code, 200)

	# 	# Assert the response data or any specific values in the response
	# 	response_data = response.get_json()
	# 	app.logger.info('response_data %s', response_data)

	# 	self.assertEqual(response_data['sentiment'], target_sentiment)

	# @parameterized.expand([
	# 	(
	# 		'simple_test',
	# 		'I lost my phone.',
	# 	)
	# 	])
	# def test_ask_for_thought(self, test_name: str, user_event: str):
	# 	"""Tests the ask_for_thought function."""

	# 	payload = {'event': user_event}

	# 	# Send a POST request to the endpoint with the sample payload.
	# 	response = self.app.post('/thought', json=payload)
	# 	app.logger.info('response %s', response)

	# 	# Assert the response status code
	# 	self.assertEqual(response.status_code, 200)

	# 	# Make sure the response is not None.
	# 	response_data = response.get_json()
	# 	self.assertIsNotNone(response)


	# # TODO(toni) Add test cases that check for belief, thought or self-talk.
	# def test_ask_for_belief_loop(self):
	# 	"""Tests the ask for thought loop function."""
	# 	payload = {
	# 	"user_event": "I have a pile of work and I just got additional emails coming in! ",
	# 	"history": [],
	# 	"last_user_response": None
	# 	}

	# 	# Send a POST request to the endpoint with the sample payload
	# 	response = self.app.post('/reflect/ask_for_belief_loop', json=payload)
	# 	app.logger.info('response %s', response)


	# def test_distortion_loop(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio

	# 	payload = {
	# 	"user_event": "I have a ton of work and I just got an email with many more TODO's ",
	# 	"belief_history": [
	# 			{
	# 					"role": "assistant",
	# 					"content": "I understand that receiving an overwhelming amount of work and a new set of tasks can be quite stressful. Can you tell me what thoughts or beliefs come up for you when faced with this situation?"
	# 			}
	# 	],
	# 	"user_belief": "I'm worried that because things keep changing it's hard for me to give definitive answers.",
	# 	"distortion_history": [],
	# 	"last_user_response": None
	# 	}

	# 	# Send a POST request to the endpoint with the sample payload
	# 	response = self.app.post('/reflect/distortion_loop', json=payload)
	# 	app.logger.info('response %s', response)

	# 	# Assert the response status code
	# 	self.assertEqual(response.status_code, 200)

	# 	# Assert the response data or any specific values in the response
	# 	response_data = response.get_json()

	# 	# TODO(toni) Add asserts when we are using the LLM.

	# def test_possitive_feedback(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {"positive_user_event": "I got all my chores done."}
	# 	response = self.app.post('/positive_feedback', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_cheer_loop(self):
	# 	"""Test the cheerleader loop."""

	# 	payload = {
	# 		'user_event': 'I didn\'t get the promotion.',
	# 		'user_identifies_person': 'Bobby',
	# 		'cheer_history': [],
	# 		'last_user_response': None
	# 	}
	# 	response = self.app.post('/cheerleader/cheer_loop', json=payload)

	# 	# Assert the response status code -- succeeded.
	# 	self.assertEqual(response.status_code, 200)


	# def test_ask_for_person(self):

	# 	payload = {'user_event': 'I gave a bad presentation.'}
	# 	response = self.app.post('/cheerleader/ask_for_person', json=payload)

	# 	# Assert the response status code -- succeeded.
	# 	self.assertEqual(response.status_code, 200)

	# def test_goal_loop(self):
	# 	"""Test the goal setting loop."""

	# 	payload = {
	# 		'user_goal': 'I want to go for a walk.',
	# 		'goal_history': [],
	# 		'last_user_response': None
	# 	}
	# 	response = self.app.post('/goal/goal_loop', json=payload)

	# 	# Assert the response status code -- succeeded.
	# 	self.assertEqual(response.status_code, 200)

	# def test_control_loop(self):
	# 	payload = {
	# 	"user_event": "Overwhelmed by my workload.",
	# 	"history": [
	# 			{
	# 					"role": "assistant",
	# 					"content": "What are the things or tasks in your workload that you have control over?"
	# 			},
	# 	],
	# 	"last_user_response": None
	# 	}

	# 	response = self.app.post('/sphere_of_influence/control_loop', json=payload)

	# 	# Assert the response status code -- succeeded.
	# 	self.assertEqual(response.status_code, 200)


	# # TODO(toni) Parametrize this.
	# def test_days_since_start(self):
	# 	# freeze_time args: YYYY-MM-DD
	# 	with freeze_time('2023-08-31'):
	# 		diff = my_app._days_since_start()
	# 		logging.info(f'diff={diff}')
	# 		assert diff == 24

	# def test_get_gratitude_prompt(self):
	# 	with freeze_time('2023-08-31'):
	# 		response = self.app.post('/gratitude_challenge/get_gratitude_prompt')

	# 		# Assert the response status code -- succeeded.
	# 		self.assertEqual(response.status_code, 200)

	# def test_create_gratitude_post(self):
	# 	with freeze_time('2023-08-31'):

	# 		paylod = {"response": "Grateful for my co-founder."}
	# 		response = self.app.post('/gratitude_challenge/create_post', json=paylod)

	# 		# Assert the response status code -- succeeded.
	# 		self.assertEqual(response.status_code, 200)

	# def test_save_goal_data(self):

	# 	payload = {
	# 	"user_goal" : "Go for a swim",
	# 	"history": [{"role": "assistant", "content": "Great! Let's make it a SMART goal. \n\nFirst, let's make it more specific. Are there any specific parameters or objectives you have in mind for this swim?"}, {"role": "user", "content": "Just want to swim for 20 minutes"}, {"role": "assistant", "content": "Perfect! That makes it a lot more specific. \n\nNow let's make it measurable. How will you track your progress throughout the 20 minutes of swimming?"}, {"role": "user", "content": "I\u2019ll use my smart watch?"}, {"role": "assistant", "content": "Excellent! Using your smartwatch to track your swim time makes it easily measurable. \n\nNext, let's make sure it is an achievable goal. Do you feel confident in your ability to complete a 20-minute swim session?"}, {"role": "user", "content": "Am I had to take some rest, but yeah I can definitely in the water for 20 minutes"}, {"role": "assistant", "content": "That's great to hear! Allowing for rests during the swim is a great way to make it achievable. \n\nNow, let's make sure the goal is relevant. Why is going for a 20-minute swim important to you today?"}, {"role": "user", "content": "I need to get back into exercise"}, {"role": "assistant", "content": "That's a fantastic reason! Getting back into exercise is an important goal. \n\nFinally, let's make it time-bound. Will you be able to complete your 20-minute swim session today?"}, {"role": "user", "content": "Yeah, after my last meeting"}, {"role": "assistant", "content": "Wonderful! So, to summarize, your SMART goal for today is: To swim for 20 minutes using your smartwatch to track your progress, allowing for rests, as a way to get back into exercise, after your last meeting.\n\nSESSION ENDED."}],
	# 	"user_feel_after" : "4",
	# 	"origin": "twilio_flow",
	# 	"flow_sid" : "FWXXXXXX",
	# 	"user_id": "whatsapp:+XXXXXXX",
	# 	"error": "None"
	# 	}

	# 	response = self.app.post('/goal/save_goal_data', json=payload)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_abc_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 	"user_feeling": "I’m frustrated.",
	# 	"bot_feeling": "{sentiment=negative}",
	# 	"user_event": "",
	# 	"user_belief": "my_belief.",
	# 	"bot_distortions": "",
	# 	"user_rephrase": "",
	# 	"user_feel_after": "4",
	# 	"user_feedback": "",
	# 	"flow_sid": "FWc07c84c47d2919c40d8561c548416e37",
	# 	"origin": "twilio_flow",
	# 	"user_id": "whatsapp:+447479813767",
	# 	"event_history": [
	# 			{
	# 					"role": "assistant",
	# 					"content": "I'm sorry to hear that you're feeling frustrated. Can you tell me what happened that made you feel this way?"
	# 			},
	# 			{
	# 					"role": "user",
	# 					"content": "event_hist_1"
	# 			},
	# 			{
	# 					"role": "assistant",
	# 					"content": "STOP EVENT DETECTED. event_summary"
	# 			}
	# 	],
	# 	"distortion_history": [
	# 			{
	# 					"role": "assistant",
	# 					"content": "distortion_hist_1"
	# 			},
	# 			{
	# 					"role": "user",
	# 					"content": "distortion_hist_2"
	# 			},
	# 			{
	# 					"role": "assistant",
	# 					"content": "distortion_hist_3"
	# 			},
	# 			{
	# 					"role": "user",
	# 					"content": "distortion_hist_4"
	# 			},
	# 			{
	# 					"role": "assistant",
	# 					"content": "distortion_hist_5"
	# 			}
	# 	],
	# 	"error": "None"
	# 	}

	# 	response = self.app.post('/save_abc_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_control_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"user_event": "I didn't get a promotion that I thought I deserved.",
	# 		"inside_loop_history": [
	# 				{
	# 						"role": "assistant",
	# 						"content": "What aspects of the promotion process do you have control over?"
	# 				},
	# 				{
	# 						"role": "user",
	# 						"content": "I can choose when I go for promo."
	# 				},
	# 		],
	# 		"outside_loop_history": [
	# 				{
	# 						"role": "assistant",
	# 						"content": "What aspects of the promotion process do you not have control over?"
	# 				},
	# 				{
	# 						"role": "user",
	# 						"content": "The criteria for promo."
	# 				},
	# 		],
	# 		"user_feel_after": "",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FW8f2ae7cf1a24a3feadc1c46fbea6816d",
	# 		"user_id": "whatsapp:+447479813767",
	# 		"error": "None"
	# 		}

	# 	response = self.app.post('/sphere_of_influence/save_control_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# # def test_new_user(self):

	# _TODAY = date.today()
	# logging.info(f'_TODAY: {_TODAY}')
	# _TOMORROW = _TODAY + timedelta(days=2)
	# logging.info(f'_TODAY: {_TODAY}')

	# @parameterized.expand([
	# 	# Using a date in which a message had been sent from the number.
	# 	('have_sent_message_today', '2023-08-17', 'No message sent.'),
	# 	# Using a future date on which a message cannot have been sent.
	# 	('have_not_sent_message_today', _TOMORROW, 'Message sent to whatsapp:+447479813767.')
	# 	])
	# def test_reminder(self, test_name: str, date: str, target_message: str):
	# 	# TODO(toni) Do with the 'with time'
	# 	payload = {
	# 		'data': {
	# 			'phone': '(+44) 07479813767',
	# 			'idx': '5'
	# 		}
	# 	}
	# 	# freeze_time args: YYYY-MM-DD
	# 	with freeze_time(date):
	# 		response = self.app.post('/reminder', json=payload)
	# 	self.assertEqual(response.json['message'], target_message)

	# 	self.assertEqual(response.status_code, 200)

	# # TODO(toni) Make tests for different dates based on 
	# # past dates with known number of interactions.
	# def test_get_streak_infographic(self):
	# 	payload  = {
	# 	'user_number': 'whatsapp:+447479813767'
	# 	}

	# 	# freeze_time args: YYYY-MM-DD
	# 	with freeze_time('2023-07-01'):
	# 		response = self.app.post('/challenge/get_streak_infographic', json=payload)
	# 	self.assertEqual(response.status_code, 200)
	# 	self.assertEqual(response.json['image_url'], 'https://storage.googleapis.com/bobby-chat-goals/day_default_of_3.jpeg')

	# def test_save_boundaries_stage1_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"results": [
	# 			["Q1", "yes"], ["Q2", "no"], ["Q3", "yes"]
	# 			],
	# 		"user_feel_after": "5",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FW8f2ae7cf1a24a3feadc1c46fbea6816d",
	# 		"user_id": "whatsapp:+447479813767",
	# 		"error": "None"
	# 		}

	# 	response = self.app.post('/boundaries_journey/stage1/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_boundaries_stage2_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"user_event": "I had to do all of Bob's work while they were off on holiday!",
	# 		"history": [
	# 				{
	# 						"role": "assistant",
	# 						"content": "I can understand why that situation might have caused some resentment. Can you tell me more about what specifically pushed your buttons in this situation? What was it about having to do all of Bob's work that bothered you?"
	# 				},
	# 				{
	# 						"role": "user",
	# 						"content": "It didn't give me enough time for my own work!"
	# 				},
	# 		],
	# 		"summary": "In a recent experience, you felt that your boundaries were pushed when you had to do all of Bob's work while they were off on holiday.",
	# 		"last_bot_response": "Alright then, we'll focus on the situation you shared today. Remember, setting boundaries and saying no can take practice, but it's an important skill for your well-being. If you find yourself in a similar situation in the future, remember that you have the right to prioritize your own work and set limits",
	# 		"user_feel_after": "5",
	# 		"user_boundary": "TIME!",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FW56a94a032e23563e51c693e871e52931",
	# 		"user_id": "whatsapp:+447479813767",
	# 		"error": "None"
	# 		}


	# 	response = self.app.post('/boundaries_journey/stage2/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)
	
	# def test_save_boundaries_stage3_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"user_event": "",
	# 		"user_summary": "In a recent experience, you felt that your boundaries were pushed when you had to do all of Bob's work while they were off on holiday.",
	# 		"history": [
	# 				{
	# 						"role": "assistant",
	# 						"content": "Let's start by identifying the emotion you felt when your boundaries were pushed. How would you describe your emotion in that situation?"
	# 				}
	# 		],
	# 		"last_bot_response": "Let's start by identifying the emotion you felt when your boundaries were pushed. How would you describe your emotion in that situation?",
	# 		"user_feel_after": "5",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FWc6127ed9c78fb9bb276eef11fad7a3cb",
	# 		"user_id": "whatsapp:+447479813767",
	# 		"error": "None"
	# 	}

	# 	response = self.app.post('/boundaries_journey/stage3/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_boundaries_stage4_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	#     "user_feedback_0": "4",
	#     "user_feedback_1": "no",
	#     "user_feedback_2": "no",
	#     "user_feedback_3": "no",
	#     "origin": "twilio_flow",
	#     "flow_sid": "FW6db47a445666b28cacd19b2730f3f131",
	#     "user_id": "whatsapp:+44747987654321",
	#     "error": "None"
	# 	}

	# 	response = self.app.post('/boundaries_journey/stage4/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_boundaries_stage5_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"user_event": "",
	# 		"user_summary": "In a recent experience, you felt that your boundaries were pushed when you had to do all of Bob's work while they were off on holiday.",
	# 		"history": [
	# 				{
	# 						"role": "assistant",
	# 						"content": "Let's start by identifying the emotion you felt when your boundaries were pushed. How would you describe your emotion in that situation?"
	# 				}
	# 		],
	# 		"last_bot_response": "Let's start by identifying the emotion you felt when your boundaries were pushed. How would you describe your emotion in that situation?",
	# 		"user_feel_after": "5",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FWc6127ed9c78fb9bb276eef11fad7a3cb",
	# 		"user_id": "whatsapp:+447479813767",
	# 		"error": "None"
	# 	}

	# 	response = self.app.post('/boundaries_journey/stage5/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_burnout_survey_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"results": [
	# 			"1", "2", "5", "4"
	# 			],
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FW8f2ae7cf1a24a3feadc1c46fbea6816d",
	# 		"user_number": "whatsapp:+447479813767",
	# 		"error": "None"
	# 		}

	# 	response = self.app.post('/burnout_survey/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# def test_save_burnout_survey_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"is_reminder_set": "Yes",
	# 		"why_not_set_reminder": None,
	# 		"user_number_of_days": "5",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FW8f2ae7cf1a24a3feadc1c46fbea6816d",
	# 		"user_id": "whatsapp:+447479813767",
	# 		"error": "None"
	# 		}

	# 	response = self.app.post('/custom_reminder/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# """ Do not include this function.
	# def test_set_custom_reminder(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"user_number_of_days": 1,
	# 		"user_number": "whatsapp:+447479813767"
	# 		}

	# 	response = self.app.post('custom_reminder/set_custom_reminder', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)"""

	# def test_save_journaling_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	# 		"prompt": "What's on your mind?",
	# 		"user_topic_intro": "Family",
	# 		"topic_history": [],
	# 		"last_user_topic_response": None,
	# 		"free_style_user_event": None,
	# 		"user_event_var": "I went skating with my family in CT",
	# 		"user_event": "I went skating with my family in CT",
	# 		"start_time": "Sat, 07 Oct 2023 11:31:11 GMT",
	# 		"history": [],
	# 		"last_user_response": "No.. it was quite a while a go.",
	# 		"approx_end_time": "Sat, 07 Oct 2023 11:32:19 GMT",
	# 		"user_feel_after": "4",
	# 		"user_unsure": None,
	# 		"user_does_not_commit": None,
	# 		"user_id": "whatsapp:+447479813767",
	# 		"origin": "twilio_flow",
	# 		"flow_sid": "FWd82d15bd01c67e7fd87dfdc1072f49b3",
	# 		"error": "None"
	# 	 }

	# 	response = self.app.post('/journaling/save_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	# Example json when a new customer is created.
	# Remove some fields for brevity.
	_CUSTOMER_ID = "cus_test"
	_CUSTOMER_CREATED_PAYLOAD = {
		"object": "event",
		"data": {
			"object": {
				"id": _CUSTOMER_ID,
				"object": "customer",
				"address": {
					"country": "GB",
				},
					"email": "toni@bobby-chat.com",
					"name": "test name",
					"phone": "+447479876534",
			}
		},
		"type": "customer.created"
	}

	_SUBSCRIPTION_CREATED_PAYLOAD = {
    "object": "event",
    "data": {
        "object": {
            "id": "sub_1O8R9sIvT4WZgIskUdQhe3kl",
            "object": "subscription",
            "customer": _CUSTOMER_ID,
            "plan": {
                "nickname": "bobbychat-monthly-£9-45",
                "product": "prod_OvqYwqTlW1X3Rp",
            },
            "start_date": 1699032468,
            "status": "trialing",
        }
    },
    "type": "customer.subscription.created"
}

	_SUBSCRIPTION_DELETED_PAYLOAD = {
		"id": "evt_1O8KhfIvT4WZgIskU1nA99kl",
		"object": "event",
		"api_version": "2023-10-16",
		"created": 1699007655,
		"data": {
				"object": {
						"cancellation_details": {
								"comment": None,
								"feedback": None,
								"reason": "cancellation_requested"
						},
						"customer": _CUSTOMER_ID,
						"plan": {
								"nickname": "bobbychat-monthly-£9-45",
								"product": "prod_OvqYwqTlW1X3Rp",
						},
						"start_date": 1698934142,
						"status": "canceled",
				}
		},
		"type": "customer.subscription.deleted"
		}

	_SUBSCRIPTION_UPDATED_PAYLOAD = {
		"id": "evt_1O8LZRIvT4WZgIskhHDAMTN0",
		"object": "event",
		"api_version": "2023-10-16",
		"created": 1699010989,
		"data": {
				"object": {
						"customer": _CUSTOMER_ID,
						"plan": {
								"nickname": "bobbychat-monthly-£9-45",
								"product": "prod_OvqYwqTlW1X3Rp",
						},
						"start_date": 1699008202,
						"status": "trialing",
				}
		},
		"type": "customer.subscription.updated"
	}

	# Buying a non-subscription product.
	_CHECKOUT_SESSION_COMPLETE_1 = {
	  "id": "evt_1OAtwxIvT4WZgIskcByI4uLa",
	  "object": "event",
	  "data": {
	    "object": {
	      "customer_details": {
	        "email": "toni@testing.com",
	        "phone": "+447479876534",
	      },
	      "customer": None,
	      "metadata": {
	        "number_of_months": "3",
	        "product": "bobby-chat-3-month-pass"
	      },
	    }
	  },
	  "type": "checkout.session.completed"
	}

	# Buying a subscription product.
	_CHECKOUT_SESSION_COMPLETE_2 = {
	  "id": "evt_1OAtwxIvT4WZgIskcByI4uLa",
	  "object": "event",
	  "data": {
	    "object": {
	      "customer_details": {
	        "email": "toni@bobby-chat.com",
	        "phone": "+447479876534",
	      },
	      "customer": _CUSTOMER_ID,
	      "metadata": {
	      },
	    }
	  },
	  "type": "checkout.session.completed"
	}

	@parameterized.expand([
		('customer.created', _CUSTOMER_CREATED_PAYLOAD),
		('checkout.session.completed', _CHECKOUT_SESSION_COMPLETE_1),
		('checkout.session.completed', _CHECKOUT_SESSION_COMPLETE_2),
		('customer.subscription.created', _SUBSCRIPTION_CREATED_PAYLOAD),
		('customer.subscription.updated', _SUBSCRIPTION_UPDATED_PAYLOAD),
		('customer.subscription.deleted', _SUBSCRIPTION_DELETED_PAYLOAD),
	])
	def test_stripe_webhook(self, name, payload):

		with app.app_context():
			response = self.app.post('/stripe_webhook', json=payload)

		response_json = response.json
		logging.info('stripe_webbook response:', response_json)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response_json['type'], name)

	# TODO(toni) Want to test different use cases -- i.e. someone has subscribed or not.
	def test_authenticate_user(self):

		with app.app_context():

			payload = {"user_number": "whatsapp:+447479876534"}

			response = self.app.post('/authenticate_user', json=payload)

		response_json = response.json
		logging.info('authenticate_user response:', response_json)
		self.assertEqual(response.status_code, 200)

	def test_why_not_buy_save_data(self):
		# Create a sample request payload to simulate the data sent by Twilio.
		payload = {
			"user_id": "whatsapp:+447479813767",
			"why_not_buy": "Test: too expensive."
			}

		response = self.app.post('/why_not_buy_save_data', json=payload)
		app.logger.info('response %s', response)
		self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
	unittest.main()





