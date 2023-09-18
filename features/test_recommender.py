"""Test the functions in recommender.py."""
import unittest
from unittest.mock import Mock
from parameterized import parameterized
from flask import Flask
import recommender
import sys

sys.path.append('..')
import utils

app = Flask(__name__)

class TestRecommender(unittest.TestCase):

	def setUp(self):
		utils.setup_openai()

	# TODO(toni) Make parametrized.
	@parameterized.expand([
		# Valid user use choices.
		('test1', 'I\'m happy'),
		('test2', 'I want to disappear'),
		('test3', 'I feel overwhelmed'),
		])
	def test_recommend_tool(self, name, user_feeling):
		# Create a mock request object
		test_request = Mock()
		test_request.json = {'user_feeling': user_feeling}

		with app.app_context():
			response = recommender.recommend_tool(test_request)

		response = response.json
		self.assertIsNotNone(response)


if __name__ == "__main__":
	unittest.main()