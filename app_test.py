import unittest
import app as my_app
from app import app
from parameterized import parameterized
import logging
from abc_types import Sentiment

class FeelingsTestCase(unittest.TestCase):

	def setUp(self):
		self.app = app.test_client()

	@parameterized.expand(
		[
		('I\'m good, thanks.', Sentiment.POS.value, ['good']),
		# ('Feeling very tired today.', 'NEG', ['tired']),
		# ('My car broke down, and I\'m feeling frustrated and stressed.',
		# 	'NEG', ['frustrated', 'stressed']),
		# ('I\'m not sure', 'NEUTRAL', ['unsure']),
		])
	def test_user_feeling(
		self,
		body: str,
		sentiment: str,
		feeling: list[str]):
	  # Create a sample request payload to simulate the data sent by 
	  # Twilio
	  payload = {'feeling': feeling}

	  # Send a POST request to the endpoint with the sample payload
	  logging.info('app:', self.app)
	  response = self.app.post('/feeling', json=payload)
	  logging.info('response %s', response)

	  # Assert the response status code
	  # self.assertEqual(response.status_code, 200)

	  # Assert the response data or any specific values in the response
	  response_data = response.get_json()

	  self.assertEqual(response_data['sentiment'], sentiment)
	  assert any(i in response_data['feelings'] for i in feeling)

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
		model_output,
		sentiment: Sentiment,
		feelings: list[str],
		event: str = None):

		output = my_app.feelings_post_process(model_output)

		self.assertEqual(output['sentiment'], sentiment)
		self.assertEqual(output['feelings'], feelings)

		if event:
			self.assertEqual(output['event'], event)

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
	def test_distortion_detection_post_processing(self,
		model_outupt,
		distortion: str,
		question: str):

		output = my_app.distortion_detection_post_processing(model_outupt)

		self.assertEqual(output['distortion'], distortion)
		self.assertEqual(output['question'], question)

	# TODO(toni) make param'ed test: 
	@parameterized.expand([
		('I\'m doomed, that I\'ve lost everything, and that I\'ll never be able to recover from this situation.'),
		('I can\'t handle everything, that I\'m drowning in responsibilities, and that there\'s no way out of this never-ending cycle.')
		])
	def test_detect_distortions(self, belief):
	  # Create a sample request payload to simulate the data sent by 
	  # Twilio
	  payload = {'belief': belief}

	  # Send a POST request to the endpoint with the sample payload
	  logging.info('app:', self.app)
	  response = self.app.post('/belief', json=payload)
	  logging.info('response %s', response)

	  # Assert the response status code
	  # self.assertEqual(response.status_code, 200)

	  # Assert the response data or any specific values in the response
	  response_data = response.get_json()

	  # TODO(toni) Add asserts when we are using the LLM.

	def test_save_abc_data(self):
		# Create a sample request payload to simulate the data sent by 
	  # Twilio
	  payload = {
	      'Body': {
	      	"user_feeling": 'dummy_user_feeling',
					"bot_feeling": dict(
						sentiment='POS', feelings=['sad'], event=None),
					"user_event": 'dummy_user_event',
					"user_belief": 'dummy_user_belief',
					"bot_distortions": dict(
						distortion='dummy_distortion',
						question='dummy_question'),
					"user_rephrase": 'dummy_user_rephrase',
					"user_easy": 'dummy_easy_score',
					"user_feel_after": 'dummy_feeling_after_score',
					"user_feedback": 'dummy_user_feedback',
					"flow_vars": 'dummy_flow_vars',
					"flow_sid": 'dummy_sid',
					"flow_variable": 'dummy_flow_variable',
					# So we know that this is a test sample.
					"origin": "test"
					},

	      'From': '+1234567890'
	  }

	  logging.info('app:', self.app)
	  response = self.app.post('/save_abc_data', json=payload)
	  logging.info('response %s', response)
	  self.assertEqual(response.status_code, 200)



if __name__ == '__main__':
    unittest.main()




