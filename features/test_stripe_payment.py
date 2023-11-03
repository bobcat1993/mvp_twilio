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
from features.stripe_payment import Status

app = Flask(__name__)

_TODAY_DATE = date.today()
_USER_NUMBER = 'whatsapp:+4476543210'
_CUSTOMER_ID = 'cus_123456765432'
_USER_EMAIL = 'antonia.creswell@gmail.com'

# Example json when a new customer is created.
# Remove some fields for brevity.
_CUSTOMER_CREATED_PAYLOAD = {
    "object": "event",
    "data": {
        "object": {
            "id": "cus_OvtMKUUtrX26ck",
            "object": "customer",
            "address": {
                "country": "GB",
            },
            "email": "toni@bobby-chat.com",
            "name": "test name",
            "phone": "+447479876534",
        }
    },
    "type": "customer.created"
}


class TestStripePayment(unittest.TestCase):

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

	def test_subscription_ends(self):

		data = [
			{
				'customer_id': _CUSTOMER_ID,
				'status': Status.ACTIVE.value
			},
		]

		target_number_of_days = 3

		# Add the dummy UserDatum to the table.
		for d in data:
			datum = ProfileDatum(**d)
			self.session.add(datum)
		self.session.commit()

		with app.app_context():
			stripe_payment.subscription_ends(
				customer_id=_CUSTOMER_ID,
				db=self,
				ProfileDatum=ProfileDatum)

		# Check that the status has changed.
		record = self.session.query(ProfileDatum).filter(ProfileDatum.customer_id == _CUSTOMER_ID).all()
		status = record[-1].status

		self.assertEqual(status, Status.CANCELLED.value)


	@parameterized.expand([
		('cancelled', 'canceled', Status.CANCELLED.value),
		('trial', 'trailing', Status.ACTIVE.value),
		('active', 'active', Status.ACTIVE.value),
		# ('incomplete', 'incomplete', Status.ACTIVE.value),
		# ('incomplete_expired', 'incomplete_expired', Status.ACTIVE.value),
		# ('past_due', 'past_due', Status.ACTIVE.value),
		# ('unpaid', 'unpaid', Status.ACTIVE.value),
		])
	def test_subscription_updated(self, name, new_status, expected_new_status):

		data = [
			{
				'customer_id': _CUSTOMER_ID,
				'status': None
			},
		]

		target_number_of_days = 3

		# Add the dummy UserDatum to the table.
		for d in data:
			datum = ProfileDatum(**d)
			self.session.add(datum)
		self.session.commit()

		with app.app_context():
			stripe_payment.subscription_updated(
				customer_id=_CUSTOMER_ID,
				new_status=new_status,
				db=self,
				ProfileDatum=ProfileDatum)

		# Check that the status has changed.
		record = self.session.query(ProfileDatum).filter(ProfileDatum.customer_id == _CUSTOMER_ID).all()
		status = record[-1].status

		self.assertEqual(status, expected_new_status)


	"""
	## TEST NOT WORKING YET CAUSE OF SIGNATURES.
	@parameterized.expand([
		('customer.created', _CUSTOMER_CREATED_PAYLOAD),
		])
	def test_stripe_webhook(self, name, payload):

		test_request = Mock()
		test_request.data = payload

		with app.app_context():
			response = stripe_payment.stripe_webhook(
				test_request, db=self, ProfileDatum=ProfileDatum)

		response = response.json
		self.assertIsNotNone(response)
		"""






if __name__ == '__main__':
	unittest.main()