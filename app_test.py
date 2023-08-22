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

	@parameterized.expand(
		[
		(
			'23:30:12',
			'I notice you are up late. How are you feeling?'
		),
		(
			'03:22:12',
			'It seems early. How are you feeling?'
		),
		(
			'10:00:14',
			'Let\'s start. How you are feeling this morning?'
		),
		(
			'14:23:23',
			'Let\'s begin. How are you feeling this afternoon?'
		),
		(
			'18:22:30',
			'Let\'s start. How have you been feeling this evening?'
		),
		])
	def test_user_feeling(
		self,
		time: str,
		target_response: str):

		with freeze_time(time):
			response = self.app.post('/user_feeling')

		# Assert the response status code
		self.assertEqual(response.status_code, 200)

		# Assert the response status code
		response_data = response.get_json()
		self.assertEqual(response_data['response'], target_response)

	@parameterized.expand(
		[
		('I\'m good, thanks.', Sentiment.POS.value),
		# Feeling tired currently seen by the model as neutral.
		# ('Feeling very tired today.', Sentiment.NEG.value),
		('My car broke down, and I\'m feeling frustrated and stressed.',
			Sentiment.NEG.value),
		('I\'m not sure', Sentiment.NEUTRAL.value),
		('I had a really fun time with my friends', Sentiment.POS.value),
		('I had so much fun, sad it\'s over', Sentiment.POS.value),
		('I\'m not sure.', Sentiment.NEUTRAL.value)
		])
	def test_detect_sentiment(
		self,
		user_feeling: str,
		target_sentiment: str):
		# Create a sample request payload to simulate the data sent by 
		# Twilio
		payload = {'feeling': user_feeling}

		# Send a POST request to the endpoint with the sample payload
		response = self.app.post('/detect_sentiment', json=payload)
		app.logger.info('response %s', response)

		# Assert the response status code
		self.assertEqual(response.status_code, 200)

		# Assert the response data or any specific values in the response
		response_data = response.get_json()
		app.logger.info('response_data %s', response_data)

		self.assertEqual(response_data['sentiment'], target_sentiment)

	@parameterized.expand([
		(
			'simple_test',
			'I lost my phone.',
		)
		])
	def test_ask_for_thought(self, test_name: str, user_event: str):
		"""Tests the ask_for_thought function."""

		payload = {'event': user_event}

		# Send a POST request to the endpoint with the sample payload.
		response = self.app.post('/thought', json=payload)
		app.logger.info('response %s', response)

		# Assert the response status code
		self.assertEqual(response.status_code, 200)

		# Make sure the response is not None.
		response_data = response.get_json()
		self.assertIsNotNone(response)


	# TODO(toni) Add test cases that check for belief, thought or self-talk.
	def test_ask_for_belief_loop(self):
		"""Tests the ask for thought loop function."""
		payload = {
		"user_event": "I have a pile of work and I just got additional emails coming in! ",
		"history": [],
		"last_user_response": None
		}

		# Send a POST request to the endpoint with the sample payload
		response = self.app.post('/reflect/ask_for_belief_loop', json=payload)
		app.logger.info('response %s', response)


	def test_distortion_loop(self):
		# Create a sample request payload to simulate the data sent by 
		# Twilio

		payload = {
		"user_event": "I have a ton of work and I just got an email with many more TODO's ",
		"belief_history": [
				{
						"role": "assistant",
						"content": "I understand that receiving an overwhelming amount of work and a new set of tasks can be quite stressful. Can you tell me what thoughts or beliefs come up for you when faced with this situation?"
				}
		],
		"user_belief": "I'm worried that because things keep changing it's hard for me to give definitive answers.",
		"distortion_history": [],
		"last_user_response": None
		}

		# Send a POST request to the endpoint with the sample payload
		response = self.app.post('/reflect/distortion_loop', json=payload)
		app.logger.info('response %s', response)

		# Assert the response status code
		self.assertEqual(response.status_code, 200)

		# Assert the response data or any specific values in the response
		response_data = response.get_json()

		# TODO(toni) Add asserts when we are using the LLM.

	def test_possitive_feedback(self):
		# Create a sample request payload to simulate the data sent by 
		# Twilio
		payload = {"positive_user_event": "I got all my chores done."}
		response = self.app.post('/positive_feedback', json=payload)
		app.logger.info('response %s', response)
		self.assertEqual(response.status_code, 200)

	def test_cheer_loop(self):
		"""Test the cheerleader loop."""

		payload = {
			'user_event': 'I didn\'t get the promotion.',
			'user_identifies_person': 'Bobby',
			'cheer_history': [],
			'last_user_response': None
		}
		response = self.app.post('/cheerleader/cheer_loop', json=payload)

		# Assert the response status code -- succeeded.
		self.assertEqual(response.status_code, 200)


	def test_ask_for_person(self):

		payload = {'user_event': 'I gave a bad presentation.'}
		response = self.app.post('/cheerleader/ask_for_person', json=payload)

		# Assert the response status code -- succeeded.
		self.assertEqual(response.status_code, 200)

	def test_goal_loop(self):
		"""Test the goal setting loop."""

		payload = {
			'user_goal': 'I want to go for a walk.',
			'goal_history': [],
			'last_user_response': None
		}
		response = self.app.post('/goal/goal_loop', json=payload)

		# Assert the response status code -- succeeded.
		self.assertEqual(response.status_code, 200)

	def test_control_loop(self):
		payload = {
    "user_event": "Overwhelmed by my workload.",
    "history": [
        {
            "role": "assistant",
            "content": "What are the things or tasks in your workload that you have control over?"
        },
    ],
    "last_user_response": None
    }

		response = self.app.post('/sphere_of_influence/control_loop', json=payload)

		# Assert the response status code -- succeeded.
		self.assertEqual(response.status_code, 200)


	# TODO(toni) Parametrize this.
	def test_days_since_start(self):
		# freeze_time args: YYYY-MM-DD
		with freeze_time('2023-08-31'):
			diff = my_app._days_since_start()
			logging.info(f'diff={diff}')
			assert diff == 24

	def test_get_gratitude_prompt(self):
		with freeze_time('2023-08-31'):
			response = self.app.post('/gratitude_challenge/get_gratitude_prompt')

			# Assert the response status code -- succeeded.
			self.assertEqual(response.status_code, 200)

	def test_create_gratitude_post(self):
		with freeze_time('2023-08-31'):

			paylod = {"response": "Grateful for my co-founder."}
			response = self.app.post('/gratitude_challenge/create_post', json=paylod)

			# Assert the response status code -- succeeded.
			self.assertEqual(response.status_code, 200)


	def test_save_goal_data(self):

		payload = {
		"user_goal" : "Go for a swim",
		"history": [{"role": "assistant", "content": "Great! Let's make it a SMART goal. \n\nFirst, let's make it more specific. Are there any specific parameters or objectives you have in mind for this swim?"}, {"role": "user", "content": "Just want to swim for 20 minutes"}, {"role": "assistant", "content": "Perfect! That makes it a lot more specific. \n\nNow let's make it measurable. How will you track your progress throughout the 20 minutes of swimming?"}, {"role": "user", "content": "I\u2019ll use my smart watch?"}, {"role": "assistant", "content": "Excellent! Using your smartwatch to track your swim time makes it easily measurable. \n\nNext, let's make sure it is an achievable goal. Do you feel confident in your ability to complete a 20-minute swim session?"}, {"role": "user", "content": "Am I had to take some rest, but yeah I can definitely in the water for 20 minutes"}, {"role": "assistant", "content": "That's great to hear! Allowing for rests during the swim is a great way to make it achievable. \n\nNow, let's make sure the goal is relevant. Why is going for a 20-minute swim important to you today?"}, {"role": "user", "content": "I need to get back into exercise"}, {"role": "assistant", "content": "That's a fantastic reason! Getting back into exercise is an important goal. \n\nFinally, let's make it time-bound. Will you be able to complete your 20-minute swim session today?"}, {"role": "user", "content": "Yeah, after my last meeting"}, {"role": "assistant", "content": "Wonderful! So, to summarize, your SMART goal for today is: To swim for 20 minutes using your smartwatch to track your progress, allowing for rests, as a way to get back into exercise, after your last meeting.\n\nSESSION ENDED."}],
		"user_feel_after" : "4",
		"origin": "twilio_flow",
		"flow_sid" : "FWXXXXXX",
		"user_id": "whatsapp:+XXXXXXX",
		"error": "None"
		}

		response = self.app.post('/goal/save_goal_data', json=payload)
		self.assertEqual(response.status_code, 200)


	def test_save_abc_data(self):
		# Create a sample request payload to simulate the data sent by 
		# Twilio
		payload = {
		"user_feeling": "I’m frustrated.",
		"bot_feeling": "{sentiment=negative}",
		"user_event": "",
		"user_belief": "my_belief.",
		"bot_distortions": "",
		"user_rephrase": "",
		"user_feel_after": "4",
		"user_feedback": "",
		"flow_sid": "FWc07c84c47d2919c40d8561c548416e37",
		"origin": "twilio_flow",
		"user_id": "whatsapp:+447479813767",
		"event_history": [
				{
						"role": "assistant",
						"content": "I'm sorry to hear that you're feeling frustrated. Can you tell me what happened that made you feel this way?"
				},
				{
						"role": "user",
						"content": "event_hist_1"
				},
				{
						"role": "assistant",
						"content": "STOP EVENT DETECTED. event_summary"
				}
		],
		"distortion_history": [
				{
						"role": "assistant",
						"content": "distortion_hist_1"
				},
				{
						"role": "user",
						"content": "distortion_hist_2"
				},
				{
						"role": "assistant",
						"content": "distortion_hist_3"
				},
				{
						"role": "user",
						"content": "distortion_hist_4"
				},
				{
						"role": "assistant",
						"content": "distortion_hist_5"
				}
		],
		"error": "None"
		}

		response = self.app.post('/save_abc_data', json=payload)
		app.logger.info('response %s', response)
		self.assertEqual(response.status_code, 200)

	def test_save_control_data(self):
	# 	# Create a sample request payload to simulate the data sent by 
	# 	# Twilio
	# 	payload = {
	#     "user_event": "I didn't get a promotion that I thought I deserved.",
	#     "inside_loop_history": [
	#         {
	#             "role": "assistant",
	#             "content": "What aspects of the promotion process do you have control over?"
	#         },
	#         {
	#             "role": "user",
	#             "content": "I can choose when I go for promo."
	#         },
	#     ],
	#     "outside_loop_history": [
	#         {
	#             "role": "assistant",
	#             "content": "What aspects of the promotion process do you not have control over?"
	#         },
	#         {
	#             "role": "user",
	#             "content": "The criteria for promo."
	#         },
	#     ],
	#     "user_feel_after": "",
	#     "origin": "twilio_flow",
	#     "flow_sid": "FW8f2ae7cf1a24a3feadc1c46fbea6816d",
	#     "user_id": "whatsapp:+447479813767",
	#     "error": "None"
	#     }

	# 	response = self.app.post('/sphere_of_influence/save_control_data', json=payload)
	# 	app.logger.info('response %s', response)
	# 	self.assertEqual(response.status_code, 200)

	_TODAY = date.today()
	logging.info(f'_TODAY: {_TODAY}')
	_TOMORROW = _TODAY + timedelta(days=2)
	logging.info(f'_TODAY: {_TODAY}')

	@parameterized.expand([
		# Using a date in which a message had been sent from the number.
		('have_sent_message_today', '2023-08-17', 'No message sent.'),
		# Using a future date on which a message cannot have been sent.
		('have_not_sent_message_today', _TOMORROW, 'Message sent to whatsapp:+447479813767.')
		])
	def test_reminder(self, test_name: str, date: str, target_message: str):
		# TODO(toni) Do with the 'with time'
		payload = {
			'data': {
				'phone': '(+44) 07479813767',
				'idx': '5'
			}
		}
		# freeze_time args: YYYY-MM-DD
		with freeze_time(date):
			response = self.app.post('/reminder', json=payload)
		self.assertEqual(response.json['message'], target_message)

		self.assertEqual(response.status_code, 200)

	# TODO(toni) Make tests for different dates based on 
	# past dates with known number of interactions.
	def test_get_streak_infographic(self):
		payload  = {
		'user_number': 'whatsapp:+447479813767'
		}

		# freeze_time args: YYYY-MM-DD
		with freeze_time('2023-07-01'):
			response = self.app.post('/challenge/get_streak_infographic', json=payload)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json['image_url'], 'https://storage.googleapis.com/bobby-chat-goals/daydefault_of_5.png')


if __name__ == '__main__':
	unittest.main()





