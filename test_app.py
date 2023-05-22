import unittest
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
	def test_your_endpoint(
		self,
		body: str,
		sentiment: str,
		feeling: list[str]):
	  # Create a sample request payload to simulate the data sent by 
	  # Twilio
	  payload = {
	      'Body': {'feeling': feeling},
	      'From': '+1234567890'
	  }

	  # Send a POST request to the endpoint with the sample payload
	  logging.info('app:', self.app)
	  response = self.app.post('/feeling', json=payload)
	  logging.info('response %s', response)

	  # Assert the response status code
	  # self.assertEqual(response.status_code, 200)

	  # Assert the response data or any specific values in the response
	  response_data = response.get_json()

	  assert 'sentiment' in response_data
	  assert 'feeling' in response_data 

	  # TODO(tonicreswell) Uncomment once hooked up to llm.
	  self.assertEqual(response_data['sentiment'], sentiment)
	  assert any(i in response_data['feeling'] for i in feeling)

if __name__ == '__main__':
    unittest.main()




