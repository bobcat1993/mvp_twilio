"""Tests for the Journaling journey/challenge."""
import unittest
from unittest.mock import Mock
import boundaries
from parameterized import parameterized
from flask import Flask, jsonify, request
from absl import logging
import os
import json
from datetime import datetime, date
from freezegun import freeze_time

import sys
sys.path.append('..')
sys.path.append('.')
import utils
from app import BoundariesStageTwoDatum, UserDatum

from journeys import journaling

app = Flask(__name__)

_TODAY_DATE = date.today()
_USER_NUMBER = 'whatsapp:+44747981767'
_USER_ID = boundaries.string_hash(_USER_NUMBER)


class TestBoundaries(unittest.TestCase):

	def setUp(self):
		utils.setup_openai()

	# TODO(toni) Parametrize this.
	def test_days_since_start(self):
		# freeze_time args: YYYY-MM-DD
		with freeze_time('2023-10-11'):
			diff = journaling._days_since_start()
			logging.info(f'diff={diff}')
			assert diff == 2

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


