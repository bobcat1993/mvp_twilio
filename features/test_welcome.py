"""Test the functions in recommender.py."""
import unittest
from unittest.mock import Mock
from parameterized import parameterized
from flask import Flask
import welcome
import sys

sys.path.append('..')
import utils

app = Flask(__name__)

class TestWelcome(unittest.TestCase):

	def setUp(self):
		utils.setup_openai()

	# TODO(toni) Make parametrized.
	@parameterized.expand([
		# Valid user use choices.
		('test1', 'What is gratitude?'),
		('test2', 'How long will it take?'),
		('test3', 'I feel overwhelmed'),
		])
	def test_recommend_tool(self, name, user_question):
		# Create a mock request object
		test_request = Mock()
		test_request.json = {'user_question': user_question}

		with app.app_context():
			response = welcome.qanda_tool(test_request)

		response = response.json
		self.assertIsNotNone(response)


if __name__ == "__main__":
	unittest.main()