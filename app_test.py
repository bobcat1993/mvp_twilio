import unittest
import app as my_app
from app import app
from parameterized import parameterized
import logging
from abc_types import Sentiment

class TestApp(unittest.TestCase):

	def setUp(self):
		self.app = app.test_client()

	@parameterized.expand(
		[
		('I\'m good, thanks.', Sentiment.POS.value, ['good']),
		('Feeling very tired today.', Sentiment.NEG.value, ['tired']),
		('My car broke down, and I\'m feeling frustrated and stressed.',
			Sentiment.NEG.value, ['frustrated', 'stressed']),
		# ('I\'m not sure', 'NEUTRAL', ['unsure']),
		])

	# TODO(toni) Reformat as target_sentiment.
	def test_user_feeling(
		self,
		user_feeling: str,
		sentiment: str,
		target_feelings: list[str]):
	  # Create a sample request payload to simulate the data sent by 
	  # Twilio
	  payload = {'feeling': user_feeling}

	  # Send a POST request to the endpoint with the sample payload
	  logging.info('app:', self.app)
	  response = self.app.post('/feeling', json=payload)
	  logging.info('response %s', response)

	  # Assert the response status code
	  self.assertEqual(response.status_code, 200)

	  # Assert the response data or any specific values in the response
	  response_data = response.get_json()

	  self.assertEqual(response_data['sentiment'], sentiment)
	  if not any(i in response_data['feelings'] for i in target_feelings):
	  	logging.warn(
	  		'%s not in %s', target_feelings, response_data['feelings'])

	@parameterized.expand(
		[
			(
				'NEG\n<feelings> Overwhelmed, helpless </feelings>',
				Sentiment.NEG.value,
				['overwhelmed', 'helpless'],
			),
			(
				'POS\n<feelings> Hopeful, proactive </feelings>',
				Sentiment.POS.value,
				['hopeful', 'proactive'],
			),
			(
				'POS\n<feelings> Good </feelings>',
				Sentiment.POS.value,
				['good'],
			),
			(
				'NEUTRAL\n<feelings> Unsure </feelings>',
				Sentiment.NEUTRAL.value,
				['unsure']
			),
			(
				'NEG\n<feelings> Not great </feelings>',
				Sentiment.NEG.value,
				['not great']
			),
			(
				(
					'NEG\n<feelings> Not great </feelings>'
					'\n<event>Lost your phone</event>'
				),
				Sentiment.NEG.value,
				['not great'],
				'lost your phone',

			),

		])
	def test_feelings_post_process(self,
		model_output: str,
		sentiment: Sentiment,
		feelings: list[str],
		event: str = None):

		output = my_app.feelings_post_process(model_output)

		self.assertEqual(output['sentiment'], sentiment)
		self.assertEqual(output['feelings'], feelings)

		if event:
			self.assertEqual(output['event'], event)


	@parameterized.expand([
		(
			'one_question',
			'<question>question_1?</question>',
			'question_1?'
		),
		(
			'two_questions',
			'<question>question_1? question_2?</question>',
			'question_1? question_2?'
		),
		(
			'two_questions_on_different_lines',
			# Questions on two lines.
			'<question>question_1?</question>'
			'\n\n<question>question_2?</question>',
			'question_1?'
		),
		(
			'two_questions_on_different_lines_with_text_inbetween',
			# Questions on two lines.
			'<question>question_1?</question>'
			'some other text'
			'\n\n<question>question_2?</question>',
			'question_1?'
		)
		])
	def test_ask_for_thought_post_processing(self,
		test_name: str, 
		model_output: str,
		target_question: str):

		output = my_app.ask_for_thought_post_processing(
			model_output)

		self.assertEqual(output['question'], target_question)


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
		logging.info('app:', self.app)
		response = self.app.post('/ask_for_thought', json=payload)
		logging.info('response %s', response)

		# Assert the response status code
		self.assertEqual(response.status_code, 200)

		# Make sure the response is not None.
		response_data = response.get_json()
		self.assertIsNotNone(response)


	@parameterized.expand(
		[
			(
				'<distortion> Catastrophizing </distortion>'
				'\n<question> What evidence is there to support the belief that you\'re doomed and will never be able to recover from this situation? </question>'
				'\n\n<distortion> Overgeneralization </distortion>'
				'\n<question> Have you faced similar situations in the past where you were able to recover? </question>'
				'\n\n<distortion> Emotional reasoning </distortion>'
				'\n<question> Are your feelings of doom and hopelessness based on facts or more on how you\'re currently feeling? </question>',
				'Catastrophizing',
				'What evidence is there to support the belief that you\'re doomed and will never be able to recover from this situation?',
			),
			(
				'<distortion> Impostor Syndrome </distortion>'
				'\n<question> Hey, can you think of any specific accomplishments or skills that demonstrate your capability and competence? </question>',
				'Impostor Syndrome',
				'Hey, can you think of any specific accomplishments or skills that demonstrate your capability and competence?'
			),
			(
				'<distortion> Negative self-beliefs </distortion>'
				'\n<question> What evidence do you have that supports the belief that you\'re not worthy of love and connection? Are there any experiences or relationships that contradict this belief? </question>',
				'Negative self-beliefs',
				'What evidence do you have that supports the belief that you\'re not worthy of love and connection? Are there any experiences or relationships that contradict this belief?'
			),
			(
				'<distortion> Personalization </distortion>\n'
				'<question> Are there any external factors or circumstances that contributed to the outcome, or are you solely responsible for the perceived failure? </question>',
				'Personalization',
				'Are there any external factors or circumstances that contributed to the outcome, or are you solely responsible for the perceived failure?'
			)

		])

	# TODO(toni) Reformat to target_question.
	# TODO(toni) Reformat to target_distortion.
	# TODO(toni) Add test_name.
	def test_distortion_detection_post_processing(self,
		model_outupt,
		distortion: str,
		question: str):

		output = my_app.distortion_detection_post_processing(model_outupt)

		self.assertEqual(output['distortion'], distortion)
		self.assertEqual(output['question'], question)

	# TODO(toni) make param'ed test: 
	@parameterized.expand([
		('I\'m doomed and I\'ve lost everything I\'ll never be able to recover from this situation.'),
		('I can\'t handle everything, that I\'m drowning in responsibilities, and that there\'s no way out of this never-ending cycle.')
		])
	# TODO(toni) Reformat as user_belief.
	def test_detect_distortions(self, belief):
		# Create a sample request payload to simulate the data sent by 
		# Twilio
		payload = {'belief': belief}

		# Send a POST request to the endpoint with the sample payload
		logging.info('app:', self.app)
		response = self.app.post('/distortions', json=payload)
		logging.info('response %s', response)

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
		logging.info('response %s', response)
		self.assertEqual(response.status_code, 200)


	def test_save_abc_data(self):
		# Create a sample request payload to simulate the data sent by 
	  # Twilio
		payload = {
			"user_feeling": "I'm pretty excited!",
			"bot_feeling": "{event=null, feelings=[excited], sentiment=positive}",
			"user_event": "",
			"user_belief": "",
			"bot_distortions": "",
			"user_rephrase": "",
			"user_easy": "",
			"user_feel_after": "",
			"user_feedback": "Nothing more from me",
			"flow_sid": "some-twilio-sid",
			"origin": "test_save_abc_data",
			"user_id": "dummy_hash"
			}

		logging.info('app:', self.app)
		response = self.app.post('/save_abc_data', json=payload)
		logging.info('response %s', response)
		self.assertEqual(response.status_code, 200)



if __name__ == '__main__':
    unittest.main()




