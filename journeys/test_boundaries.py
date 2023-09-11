"""Tests for the boundaries journey."""
import unittest
from unittest.mock import Mock
import boundaries
from parameterized import parameterized
from flask import Flask, jsonify, request
from absl import logging
import os
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

import sys
sys.path.append('..')
import utils
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import BoundariesStageTwoDatum, UserDatum

app = Flask(__name__)


# class TestBoundaries(unittest.TestCase):

# 	def setUp(self):
# 		utils.setup_openai()

# 	# TODO(toni) Make parametrized.
# 	def test_get_quiz_infographic(self):
# 		# Create a mock request object
# 		test_request = Mock()
# 		test_request.json = {}
# 		test_request.json['results'] = [
# 		"Yes", "yes", "YES", "yes!", "no", "No", 'blah']
# 		test_request.json['user_number'] = 'whatsapp:+447987654321' 
# 		expected_output = {
# 			"num_yes": 4,
# 			"num_no": 2
# 		}

# 		with app.app_context():
# 			response = boundaries.get_quiz_infographic(test_request)

# 		response = response.json
# 		self.assertEqual(
# 			response['num_yes'], expected_output['num_yes'])
# 		self.assertEqual(
# 			response['num_no'], expected_output['num_no'])

# 	_PAYLOAD_FIRST = {
# 			'history': [],
# 			'user_event': 'I took on Bob\'s work while they were on holiday.',
# 			'last_user_response': None
# 		}
# 	_PAYLOAD_LAST = {
# 		"user_event": "Yeah... I ended up doing Bob's work while he was on holiday.",
# 		"history": [
# 				{
# 						"role": "assistant",
# 						"content": "I can understand why that might have caused some resentment. When you were doing Bob's work, what specifically pushed your buttons or made you feel uncomfortable?"
# 				},
# 				{
# 						"role": "user",
# 						"content": "I had my own work to do and I was not able to priotitise it."
# 				},
# 				{
# 						"role": "assistant",
# 						"content": "I see. So the feeling of not being able to prioritize your own work was what pushed your buttons. In that moment, how did you respond to the situation?"
# 				},
# 				{
# 						"role": "user",
# 						"content": "I didn't."
# 				},
# 				{
# 						"role": "assistant",
# 						"content": "I see. It sounds like you didn't speak up or express your feelings in that moment. Looking back on it now, is there anything you wish you had done differently in that situation?"
# 				},
# 				{
# 						"role": "user",
# 						"content": "I wish I had said no...but I'm not sure how."
# 				},
# 				{
# 						"role": "assistant",
# 						"content": "I understand. It can be challenging to assert ourselves and set boundaries, especially when we're caught off guard. In this situation, where would you like to feel more boundaried? Is it in saying no to taking on someone else's work?"
# 				}
# 		],
# 		"last_user_response": "Yes!!!"
# 		}
# 	@parameterized.expand([
# 		('first', _PAYLOAD_FIRST, 1),
# 		('last', _PAYLOAD_LAST, 9),
# 		])
# 	def test_resentmemt_loop(self, name, payload, expected_len_history):
# 		# Create a mock request object
# 		test_request = Mock()

# 		test_request.json = payload

# 		with app.app_context():
# 			response = boundaries.resentmemt_loop(test_request)

# 		response = response.json
# 		history = json.loads(response['history'])
# 		self.assertEqual(len(history), expected_len_history)

today_date = date.today()
user_number = 'whatsapp:+44747981767'
user_id = boundaries.string_hash(user_number)


# class TestRetrieveSummaryFunction(unittest.TestCase):

# 	def setUp(self):
# 		# Create an SQLite in-memory database for testing
# 		self.engine = create_engine('sqlite:///:test:')
# 		BoundariesStageTwoDatum.metadata.create_all(self.engine)
# 		Session = sessionmaker(bind=self.engine)
# 		self.session = Session()

# 	def tearDown(self):
# 		# Clean up the database and close the session
# 		self.session.close()
# 		BoundariesStageTwoDatum.metadata.drop_all(self.engine)

# 	def test_gets_correct_users_summary(self):
# 		# Add two rows of data.
# 		# The user data.
# 		summary_data_1 = BoundariesStageTwoDatum(user_id=user_id, summary='This is a test summary', time=today_date)
# 		self.session.add(summary_data_1)

# 		# A distraction data.
# 		summary_data_2 = BoundariesStageTwoDatum(user_id='1234', summary='This is a wrong summary', time=today_date)
# 		self.session.add(summary_data_2)
# 		self.session.commit()

# 		# Make sure we retrieve data for the correct user.
# 		result = boundaries._retrieve_the_summary(user_id, db=self, BoundariesStageTwoDatum=BoundariesStageTwoDatum)
# 		self.assertEqual(result, 'This is a test summary')

# 	def test_gets_latest_summary(self):
# 		# Add two rows of data.
# 		# The first user data for the user_id.
# 		summary_data_1 = BoundariesStageTwoDatum(user_id=user_id, summary='This an old summary', time=today_date)
# 		self.session.add(summary_data_1)

# 		# The second user data at later time for the same user_id.
# 		summary_data_2 = BoundariesStageTwoDatum(user_id=user_id, summary='This is the latest summary', time=today_date + timedelta(days=2))
# 		self.session.add(summary_data_2)
# 		self.session.commit()

# 		# Make sure we retrieve the latest summary.
# 		result = boundaries._retrieve_the_summary(
# 			user_id,
# 			db=self,
# 			BoundariesStageTwoDatum=BoundariesStageTwoDatum)
# 		self.assertEqual(result, 'This is the latest summary')

# 	def test_gets_latest_summary(self):
# 		# Add two rows of data.
# 		# User data for the user_id.
# 		summary_data = BoundariesStageTwoDatum(user_id=user_id, summary='This is test a summary', time=today_date)
# 		self.session.add(summary_data)

# 		# Make sure we retrieve the latest summary.
# 		result = boundaries._retrieve_the_summary(
# 			user_number,
# 			db=self,
# 			BoundariesStageTwoDatum=BoundariesStageTwoDatum)
# 		self.assertEqual(result, 'This is test a summary')

# class TestIStatements(unittest.TestCase):

# 	def setUp(self):
# 		utils.setup_openai()

# 	_PAYLOAD_FIRST_WITH_SUMMARY = {
# 		"user_event": "",
# 		"user_summary": "In a recent experience, you felt that your boundaries were pushed when you had to do all of Bob's work while they were off on holiday.",
# 		"history": [],
# 		"last_user_response": None
# 		}

# 	_PAYLOAD_FIRST_WITH_OUT_SUMMARY = {
# 		"user_event": "I had to do all of Bob's work while he was off on holiday.",
# 		"user_summary": "",
# 		"history": [],
# 		"last_user_response": None
# 		}

# 	@parameterized.expand([
# 		('first', _PAYLOAD_FIRST_WITH_SUMMARY, 1),
# 		('last', _PAYLOAD_FIRST_WITH_OUT_SUMMARY, 1),
# 		])
# 	def test_i_statement_loop(self, name, payload, expected_len_history):
# 		# Create a mock request object
# 		test_request = Mock()

# 		test_request.json = payload

# 		with app.app_context():
# 			response = boundaries.i_statement_loop(test_request)

# 		response = response.json
# 		history = json.loads(response['history'])
# 		self.assertEqual(len(history), expected_len_history)


# class TestEmpatheticAssertiveness(unittest.TestCase):

# 	def setUp(self):
# 		utils.setup_openai()

# 	# Payloads for Worst Case (WC)
# 	_WC_PAYLOAD_FIRST = {
# 		"user_event": "I had to do all of Bob's work while he was off on holiday.",
# 		"user_summary": "",
# 		"history": [],
# 		"last_user_response": None
# 		}

# 	@parameterized.expand([
# 		('first', _WC_PAYLOAD_FIRST, 1),
# 		])
# 	def test_worst_case_loop(self, name, payload, expected_len_history):
# 		# Create a mock request object
# 		test_request = Mock()

# 		test_request.json = payload

# 		with app.app_context():
# 			response = boundaries.worst_case_loop(test_request)

# 		response = response.json
# 		history = json.loads(response['history'])
# 		self.assertEqual(len(history), expected_len_history)

# 	# Payloads for Empathetic Assertion (EA)
# 	_EA_PAYLOAD_FIRST = {
#     "user_event": "I was given an assignment outside of my working hours",
#     "history": [
#         {
#             "role": "assistant",
#             "content": "I understand how that can feel like your boundaries were crossed. To help you identify who you need to talk to about this situation, could you please provide some more details? For example, who assigned you the task? Was it a supervisor, a colleague, or someone else?"
#         },
#         {
#             "role": "user",
#             "content": "My boss."
#         },
#         {
#             "role": "assistant",
#             "content": "Thank you for sharing that information. What is the absolute worst outcome you can envision if you were to talk to your boss about this matter?"
#         },
#         {
#             "role": "user",
#             "content": "They might tell me I’m lazy and don’t care about my job … when I really do"
#         },
#     ],
#     "last_user_response": None
# 	}

# 	@parameterized.expand([
# 		('first', _EA_PAYLOAD_FIRST, 4),
# 		])
# 	def test_empathetic_assertion_loop(self, name, payload, expected_len_history):
# 		# Create a mock request object
# 		test_request = Mock()

# 		test_request.json = payload

# 		with app.app_context():
# 			response = boundaries.worst_case_loop(test_request)

# 		response = response.json
# 		history = json.loads(response['history'])
# 		self.assertEqual(len(history), expected_len_history)

class TestGetBoundariesStage(unittest.TestCase):

	def setUp(self):
		# Create an SQLite in-memory database for testing
		self.engine = create_engine('sqlite:///:test:')
		UserDatum.metadata.create_all(self.engine)
		Session = sessionmaker(bind=self.engine)
		self.session = Session()

	def tearDown(self):
		# Clean up the database and close the session
		self.session.close()
		UserDatum.metadata.drop_all(self.engine)

	# TODO(toni) Make param'ed test where examples exist and don't.
	def test_get_boundaries_stage(self):
		# Create some dummy data samples for UserDatum.
		data = [
			{'user_number': user_id, 'flow_name': 'boundaries-stage1'},
			{'user_number': user_id, 'flow_name': 'boundaries-stage2'},
			{'user_number': user_id, 'flow_name': 'boundaries-stage3'},
			{'user_number': user_id, 'flow_name': 'boundaries-stage2'}
		]

		target_stage = 3

		# Add the dummy UserDatum to the table.
		for d in data:
			user_datum = UserDatum(**d)
			self.session.add(user_datum)
		self.session.commit()

		# Make a dummy request.
		payload = {'user_number': user_number}
		test_request = Mock()
		test_request.json = payload

		# Make sure we retrieve data for the correct user.
		with app.app_context():
			result = boundaries.get_boundaries_stage(request=test_request, db=self, UserDatum=UserDatum)

		result = result.json
		logging.info(result)
		self.assertEqual(result['latest_stage'], target_stage)


if __name__ == "__main__":
	unittest.main()