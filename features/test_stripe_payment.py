"""Tests for the stripe payment code."""

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
from app import ProfileDatum

from features import stripe_payment

app = Flask(__name__)

_TODAY_DATE = date.today()
_USER_NUMBER = 'whatsapp:+4476543210'
_CUSTOMER_ID = 'cus_123456765432'
_USER_EMAIL = 'antonia.creswell@gmail.com'


class TestJournaling(unittest.TestCase):

	def setUp(self):
		# Setup the OpenAI key.
		utils.setup_openai()

		# Create an SQLite in-memory database for testing
		self.engine = create_engine('sqlite:///:test:')
		ProfileDatum.metadata.create_all(self.engine)
		Session = sessionmaker(bind=self.engine)
		self.session = Session()

	def tearDown(self):
		# Clean up the database and close the session
		self.session.close()
		ProfileDatum.metadata.drop_all(self.engine)

	def test_new_user(self):

		with app.app_context():
			stripe_payment.new_user(
				customer_id=_CUSTOMER_ID,
				user_number=_USER_NUMBER,
				user_email=_USER_EMAIL,
				db=self,
				ProfileDatum=ProfileDatum)




if __name__ == '__main__':
	unittest.main()