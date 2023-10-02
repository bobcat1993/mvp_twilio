"""Test functions from burnout_survey.py"""
import unittest
from unittest.mock import Mock
from parameterized import parameterized
from flask import Flask
import burnout_survey
import sys

_USER_NUMBER = 'whatsapp:+44987654321'

sys.path.append('..')
sys.path.append('')
import utils

app = Flask(__name__)

class TestBurnoutSurvey(unittest.TestCase):

	def setUp(self):
		utils.setup_openai()

	# TODO(toni) Make parametrized.
	@parameterized.expand([
		# Valid user use choices.
		('all_5s', ['5'] * 12, 1.0),
		('all_0s', ['0'] * 12, 0.0),
		('some_missig', ['5', 'not sure', '3'], 8./10),
		])
	def test_get_burnout_infographic(self, name, results, target_score):
		# Create a mock request object
		test_request = Mock()
		test_request.json = {
			'results': results,
			'user_number': _USER_NUMBER
			}

		with app.app_context():
			response = burnout_survey.get_burnout_infographic(test_request)

		response = response.json
		self.assertIsNotNone(response)
		self.assertEqual(response['percent_burnout'], target_score)
		self.assertEqual(response['wellbeing_score'], 1 - target_score)


if __name__ == "__main__":
	unittest.main()