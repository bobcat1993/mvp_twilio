"""Tests for the Journaling journey/challenge."""
import unittest
from unittest.mock import Mock
from parameterized import parameterized
from flask import Flask, jsonify, request
from absl import logging
import os
import json
from datetime import datetime, date
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append('..')
sys.path.append('.')
import utils
from app import JournalingDatum

from features import journaling

app = Flask(__name__)

_TODAY_DATE = date.today()
_USER_NUMBER = 'whatsapp:+4476543210'
_USER_ID = journaling.string_hash(_USER_NUMBER)


class TestJournaling(unittest.TestCase):


	def setUp(self):
		# Setup the OpenAI key.
		utils.setup_openai()

		# Create an SQLite in-memory database for testing
		self.engine = create_engine('sqlite:///:test:')
		JournalingDatum.metadata.create_all(self.engine)
		Session = sessionmaker(bind=self.engine)
		self.session = Session()

	def tearDown(self):
		# Clean up the database and close the session
		self.session.close()
		JournalingDatum.metadata.drop_all(self.engine)

	def test_get_number_of_days_journaled(self):
		# Create some dummy data samples for UserDatum.
		data = [
			{'user_id': _USER_ID},
			{'user_id': 'other_id'},
			{'user_id': _USER_ID},
			{'user_id': _USER_ID}
		]

		target_number_of_days = 3

		# Add the dummy UserDatum to the table.
		for d in data:
			datum = JournalingDatum(**d)
			self.session.add(datum)
		self.session.commit()

		# Make sure we retrieve data for the correct user.
		with app.app_context():
			result = journaling.get_number_of_days_journaled(user_number=_USER_NUMBER, db=self, JournalingDatum=JournalingDatum)

		self.assertEqual(result, target_number_of_days)

	_EXPECTED_URL = "https://storage.googleapis.com/bobby-chat-journaling/day{day_no}.png"

	@parameterized.expand([
		('day1', '2023-10-09', '1',  0, _EXPECTED_URL.format(day_no=1)),
		('day2', '2023-10-10', '2', 1,  _EXPECTED_URL.format(day_no=2)),
		('day3', '2023-10-11', '3', 2,  _EXPECTED_URL.format(day_no=3)),
		('day4', '2023-10-12', '4', 3,  _EXPECTED_URL.format(day_no=4)),
		('day5', '2023-10-13', '5', 4,  _EXPECTED_URL.format(day_no=5)),
		('day6', '2023-10-14', '6', 5,  _EXPECTED_URL.format(day_no=6)),
		('day7', '2023-10-15', '7', 6, _EXPECTED_URL.format(day_no=7)),
		('day8', '2023-10-16', '8', 0, _EXPECTED_URL.format(day_no=8)),
		('day_minus_1', '2023-10-08', '1', 0,  _EXPECTED_URL.format(day_no=1)),
		])
	def test_get_journal_prompt(self, name, current_date, expected_day, expected_idx, expected_url):

		test_request = Mock()
		test_request.json = {}

		with freeze_time(current_date):
			with app.app_context():
				response = journaling.get_journal_prompt(test_request)

			# Asser the day and URL are correct.
			response = response.json
			self.assertEqual(response['day'], expected_day)
			self.assertEqual(response['idx'], expected_idx)
			self.assertEqual(response['prompt_url'], expected_url)

	# TODO(do a test where the history length is 8.)
	def test_ask_follow_questions_loop(self):

	# 	test_request = Mock()
	# 	test_request.json = {
	# 	"prompt": "How was your day?",
	# 	"user_event": "Fine",
	# 	"follow_up_questions": "What did you do?\nWho were you with?",
	# 	"history": [],
	# 	"last_user_response": None
	# 	}

	# 	with app.app_context():
	# 		response = journaling.ask_follow_up_questions_loop(test_request)


if __name__ == '__main__':
	unittest.main()


