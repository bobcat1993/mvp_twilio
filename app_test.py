import unittest
import app as my_app
from app import app
from parameterized import parameterized
from abc_types import Sentiment
import logging

# See all the logs.
app.logger.setLevel(logging.INFO)

class TestApp(unittest.TestCase):

	def setUp(self):
		app.config['TESTING'] = True
		app.config['DEBUG'] = True 
		self.app = app.test_client()


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
		response = self.app.post('/thought', json=payload)
		app.logger.info('response %s', response)

		# Assert the response status code
		self.assertEqual(response.status_code, 200)

		# Make sure the response is not None.
		response_data = response.get_json()
		self.assertIsNotNone(response)

	@parameterized.expand([
    ("I’m excited for the potential benefits but I’m also worried that there will be a lot of bugs.",
    	[],
    	None
    ),
    ("I’m excited for the potential benefits but I’m also worried that there will be a lot of bugs.",
    	[{"role": "assistant", "content": "It's understandable to have such concerns. But do you think it's fair to assume that there will definitely be a lot of bugs even before giving it a chance?"}],
    	"I think that there will be a lot of bugs!"
    ),
		])
	# TODO(toni) Reformat as user_belief.
	def test_distortion_loop(
		self,
		user_belief,
		distortion_history,
		last_user_response):
		# Create a sample request payload to simulate the data sent by 
		# Twilio
		payload = {
		'user_belief': user_belief,
		"distortion_history": distortion_history,
    "last_user_response": last_user_response}

		# Send a POST request to the endpoint with the sample payload
		response = self.app.post('/distortion_loop', json=payload)
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
			"event_history": [
        {
          "role": "assistant",
          "content": "That’s great to hear! Is there anything on your mind that you would like to talk about?"
          }
        ],
			"user_id": "dummy_hash"
			}
		response = self.app.post('/save_abc_data', json=payload)
		app.logger.info('response %s', response)
		self.assertEqual(response.status_code, 200)



if __name__ == '__main__':
    unittest.main()




