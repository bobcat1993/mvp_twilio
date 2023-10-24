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

	def test_get_most_recent_topic_and_topic_idx(self):
		# Create some dummy data samples for UserDatum.
		data = [
			{'user_id': _USER_ID, 'topic': 'Time Management', 'topic_idx': 5},
			{'user_id': _USER_ID, 'topic': 'Time Management', 'topic_idx': 6},
			{'user_id': _USER_ID,'topic': 'Social Media', 'topic_idx': 0}
		]

		target_topic = 'Social Media'
		target_topic_idx = 0

		# Add the dummy UserDatum to the table.
		for d in data:
			datum = JournalingDatum(**d)
			self.session.add(datum)
		self.session.commit()

		# Make sure we retrieve data for the correct user.
		with app.app_context():
			result = journaling.get_most_recent_topic_and_topic_idx(user_number=_USER_NUMBER, db=self, JournalingDatum=JournalingDatum)

		# Assert that the topic and topic idx are as expected.
		self.assertEqual(result['topic'], target_topic)
		self.assertEqual(result['topic_idx'], target_topic_idx)

		# Drop all values from the JournalingDatum.
		JournalingDatum.metadata.drop_all(self.engine)

	_EXPECTED_URL = "https://storage.googleapis.com/bobby-chat-journaling/day{day_no}.png"

	# TODO(toni) Make parametrised!
	# Test that topic and topic_idx go to None when the topic_idx is 6 (at the end of the list).
	def test_get_journal_prompt(self):

		test_request = Mock()
		test_request.json = {'user_number': _USER_NUMBER}

		# Add day_number entries.
		data = [{'user_id': _USER_ID, 'topic': 'Friendships', 'topic_idx': 5}]

		# Add the dummy UserDatum to the table.
		for d in data:
			datum = JournalingDatum(**d)
			self.session.add(datum)
		self.session.commit()

		with app.app_context():
			response = journaling.get_journal_prompt(test_request, db=self, JournalingDatum=JournalingDatum)

		# Assert the day and URL are correct.
		response = response.json
		self.assertEqual(response['topic'], 'Friendships')
		self.assertEqual(response['topic_idx'], 6)

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

	def test_ask_user_for_journaling_topic_loop(self):

		test_request = Mock()
		test_request.json = {
			'user_topic_intro': 'I want to manage my time better.',
			'history': [],
			'last_user_response': None}

		expected_topic = 'Time Management'
		expected_topic_idx = 0

		with app.app_context():
			response = journaling.ask_user_for_journaling_topic_loop(test_request)

		# It's possible that the bot tries to confirm the choice and hence this is not the last response.
		response = response.json
		if response['is_done'] == True:
			self.assertEqual(response['topic'], expected_topic)
			self.assertEqual(response['topic_idx'], expected_topic_idx)


if __name__ == '__main__':
	unittest.main()


