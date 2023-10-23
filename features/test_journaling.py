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

		# Drop all values from the JournalingDatum.
		JournalingDatum.metadata.drop_all(self.engine)

	_EXPECTED_URL = "https://storage.googleapis.com/bobby-chat-journaling/day{day_no}.png"

	def test_get_journal_prompt(self, day_number=4):

		test_request = Mock()
		test_request.json = {'user_number': _USER_NUMBER}

		# Add day_number entries.
		data = [{'user_id': _USER_ID}] * day_number

		# Add the dummy UserDatum to the table.
		for d in data:
			datum = JournalingDatum(**d)
			self.session.add(datum)
		self.session.commit()

		with app.app_context():
			response = journaling.get_journal_prompt(test_request, db=self, JournalingDatum=JournalingDatum)

		# Asser the day and URL are correct.
		response = response.json
		self.assertEqual(response['day'], str(day_number))
		self.assertEqual(response['idx'], day_number - 1)

		# Remove any values from the journaling data.
		JournalingDatum.metadata.drop_all(self.engine)

	# TODO(do a test where the history length is 8.)
	def test_ask_follow_questions_loop(self):

		test_request = Mock()
		test_request.json = {
		"prompt": "How was your day?",
		"user_event": "Fine",
		"follow_up_questions": "What did you do?\nWho were you with?",
		"history": [],
		"last_user_response": None
		}

		with app.app_context():
			response = journaling.ask_follow_up_questions_loop(test_request)


if __name__ == '__main__':
	unittest.main()

