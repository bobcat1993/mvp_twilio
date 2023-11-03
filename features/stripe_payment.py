"""Functions to process Stripe Payment Webhooks."""

import json
import os
import stripe
from dotenv import load_dotenv
import datetime
from absl import logging

from flask import Flask, jsonify, request
from enum import Enum
import requests

load_dotenv()

class Status(Enum):
	ACTIVE = 'active'
	TRIAL = 'trialling'
	CANCELLED = 'cancelled'


STRIPE_API_KEY = os.environ['STRIPE_API_KEY']
# Endpoint's secret can be found in the webhook settings in the Developer Dashboard.
STRIPE_SECRET = os.environ['STRIPE_SECRET']


def time_from_timestamp(timestamp):
	return datetime.datetime.utcfromtimestamp(timestamp)


def get_event(request):
	"""Gets the event from the request verifying the signature."""
	event = None
	payload = request.data

	try:
		event = json.loads(payload)
	except json.decoder.JSONDecodeError as e:
		print('⚠️  Webhook error while parsing basic request.' + str(e))
		return jsonify(success=False)

	# Make sure that the request is coming from Stripe.
	if STRIPE_SECRET != 'None':
		# Locally the strip secrete will be None for testing, but will not
		sig_header = request.headers['STRIPE_SIGNATURE']
		try:
				event = stripe.Webhook.construct_event(
						payload, sig_header, STRIPE_SECRET
				)
		except ValueError as e:
				# Invalid payload
				raise e
		except stripe.error.SignatureVerificationError as e:
				# Invalid signature
				raise e
	return event

def new_user(customer_id, user_number, user_email, db, ProfileDatum):
	"""Adds new users to the user Profile database."""

	user_number = f'whatsapp:{user_number}'

	# The data
	data = dict(
		customer_id=customer_id,
		user_number=user_number,
		user_email=user_email,
		status=Status.ACTIVE.value,
		)

	# Check if there is already an entry for this person:
	record = db.session.query(ProfileDatum).filter(ProfileDatum.user_email == user_email).first()

	logging.info("[RECORD] %s", record)

	if record:
		record.user_number = user_number
		db.session.commit()

	else:
		profile_datum = ProfileDatum(**data)
		db.session.add(profile_datum)
		db.session.commit()

	# Add contact to EmailOctopus
	api_key = str(os.environ['EMAIL_OCTOPUS_API_KEY']).strip()

	headers = {
		'Content-Type': 'application/json',
	}

	data = (
		'{"api_key":'
		f'"{api_key}",'
		f'"email_address": "{user_email}",'
		'"status":"SUBSCRIBED"}'
		)

	list_id = "6a120b2e-2c6a-11ee-b889-9147f389737a"
	response = requests.post(f'https://emailoctopus.com/api/1.6/lists/{list_id}/contacts', headers=headers, data=data)

	response_dict = json.loads(response.text)
	logging.info('Request to EmailOctopus: %s', str(response.status_code))

	return response_dict

def subscription_ends(customer_id, db, ProfileDatum):

	# Find this user.
	record = db.session.query(ProfileDatum).filter(ProfileDatum.customer_id == customer_id).all()

	logging.info("[RECORD] %s", record)

	if record:
		# Update the record to reflect that the subscription has been cancelled.
		record[-1].status = Status.CANCELLED.value
		db.session.commit()
		return

	else:
		raise ValueError('No customer %s found in Profile database.', customer_id)

def subscription_updated(customer_id, new_status, db, ProfileDatum):

	# Find this user.
	record = db.session.query(ProfileDatum).filter(ProfileDatum.customer_id == customer_id).all()

	logging.info("[RECORD] %s", record)

	if record:
		# Note that this is misspelled in Stripe.
		if new_status == 'canceled':
			# Update the record to reflect that the subscription has been cancelled.
			record[-1].status = Status.CANCELLED.value
		else:
			# For now only allow the subscription to be active or cancelled and err on the side of caution.
			record[-1].status = Status.ACTIVE.value
		db.session.commit()
		return record[-1].status

	else:
		raise ValueError('No customer %s found in Profile database.', customer_id)

#TODO(toni): split this in to different functions to update the 
# profile database as needed.
def stripe_webhook(request, db, ProfileDatum):

	event = get_event(request)

	# Handle the event
	if event['type'] == 'customer.created':
		# There is a new customer.
		data = event['data']['object']
		customer_id = data['id']
		user_email = data['email']
		user_number = data['phone']

		# Create a new user and add them to email octopus as well as the profile data.
		response_dict = new_user(customer_id, user_number, user_email, db, ProfileDatum)
		return jsonify(email_octopus=response_dict, type='customer.created'), 200
	elif event['type'] == 'customer.subscription.created':
		data = event['data']['object']
		# TODO(toni) Use this to monitor the status!
		# For now we will simply verify when a new customer is created.
	elif event['type'] == 'customer.subscription.deleted':
		# A subscription has been cancelled.
		data = event['data']['object']
		customer_id = data['customer']

		try:
			subscription_ends(customer_id, db, ProfileDatum)
			message = f'Updated status of {customer_id} to CANCELLED.'
			return jsonify(message=message, type='customer.subscription.deleted'), 200
		except Exception as e:
			return jsonify({'error': str(e)}), 400

		# TODO(toni) Collect the reasons for cancelling.

	elif event['type'] == 'customer.subscription.updated':
		# This is needed in case the user renews their subscription.
		data = event['data']['object']
		customer_id = data['customer']
		new_status = data['status']

		try:
			new_status = subscription_updated(customer_id, new_status, db, ProfileDatum)
			message = f'Updated status of {customer_id} to {new_status}.'
			return jsonify(message=message, new_status=new_status, type='customer.subscription.updated'), 200
		except Exception as e:
			return jsonify({'error': str(e)}), 400
	else:
		print('Unhandled event type {}'.format(event['type']))

	return jsonify(success=True), 400



