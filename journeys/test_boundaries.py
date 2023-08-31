"""Tests for the boundaries journey."""
import unittest
from unittest.mock import Mock
import boundaries
from flask import Flask, jsonify, request
from absl import logging
import os


app = app = Flask(__name__)

class TestBoundaries(unittest.TestCase):

	# TODO(toni) Make parametrized.
	def test_get_quiz_infographic(self):
		# Create a mock request object
		test_request = Mock()
		test_request.json = {}
		test_request.json['results'] = [
		"Yes", "yes", "YES", "yes!", "no", "No", 'blah']
		test_request.json['user_number'] = 'whatsapp:+447987654321' 
		expected_output = {
			"num_yes": 4,
			"num_no": 2
		}

		with app.app_context():
			response = boundaries.get_quiz_infographic(test_request)

		response = response.json
		self.assertEqual(
			response['num_yes'], expected_output['num_yes'])
		self.assertEqual(
			response['num_no'], expected_output['num_no'])


if __name__ == "__main__":
	unittest.main()