import unittest
from unittest.mock import Mock
from boundaries import get_quiz_infographic  # Replace with the actual import path
from flask import Flask, jsonify, request
from absl import logging

# See all the logs.
my_app = Flask(__name__)
my_app.logger.setLevel(logging.INFO)

class TestBoundaries(unittest.TestCase):

	# TODO(toni) Make parametrized.
	def test_get_quiz_infographic(self):
		# Create a mock request object
		test_request = Mock()
		test_request.json = {}
		test_request.json['results'] = [
		"Yes", "yes", "YES", "yes!", "no", "No"]
		expected_output = {
			"num_yes": 4,
			"num_no": 2
		}

		with my_app.app_context():
			response = get_quiz_infographic(test_request)

		response = response.json
		self.assertEqual(
			response['num_yes'], expected_output['num_yes'])
		self.assertEqual(
			response['num_no'], expected_output['num_no'])


if __name__ == "__main__":
	unittest.main()