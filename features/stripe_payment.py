"""Functions to process Stripe Payment Webhooks."""

import json
import os
import stripe
from dotenv import load_dotenv
import datetime
from absl import logging
from hashlib import md5

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

# TODO(toni) Move to utils.
def string_hash(string):
	return md5(string.encode()).hexdigest()

def get_WhyNotBuy(db):
	class WhyNotBuy(db.Model):
		"""Stores the data from the journaling journey flow."""

		id = db.Column(db.Integer, primary_key=True)
		user_id = db.Column(db.String, nullable=True)
		time = db.Column(db.DateTime, nullable=True)
		why_not_buy = db.Column(db.String, nullable=True)

	return WhyNotBuy


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
	record = db.session.query(ProfileDatum).filter(ProfileDatum.user_email == user_email).all()

	logging.info("[RECORD] %s", record)

	if record:
		record[-1].customer_id = customer_id
		record[-1].user_number = user_number
		record[-1].status = Status.ACTIVE.value
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
		'"fields": { "Phone" : "' + user_number + '"},'
		'"status":"SUBSCRIBED"}'
		)

	list_id = "db96a3d0-7cb1-11ee-8609-d7685fc20d35"
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
		raise ValueError(f'No customer, {customer_id}, found in Profile database.')

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
		raise ValueError(f'No customer, {customer_id}, found in Profile database.')

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
		return jsonify(email_octopus=response_dict, type='customer.created', customer_id=customer_id), 200
	elif event['type'] == 'customer.subscription.created':
		data = event['data']['object']
		customer_id = data['customer']
		status = data['status']
		try:
			# Re-using the subscription_updated function.
			status = subscription_updated(customer_id, status, db, ProfileDatum)
			message = f'New subscription: Customer {customer_id} is {status}.'
			return jsonify(message=message, status=status, type='customer.subscription.created', customer_id=customer_id), 200
		except Exception as e:
			return jsonify({'error': str(e)}), 400
	elif event['type'] == 'customer.subscription.deleted':
		# A subscription has been cancelled.
		# TODO(toni) The customer ID does not appear to match any more.
		# TODO(toni) Might need to use the subscription ID.
		data = event['data']['object']
		customer_id = data['customer']

		try:
			subscription_ends(customer_id, db, ProfileDatum)
			message = f'Updated status of {customer_id} to CANCELLED.'
			return jsonify(message=message, type='customer.subscription.deleted', customer_id=customer_id), 200
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
			return jsonify(message=message, new_status=new_status, type='customer.subscription.updated', customer_id=customer_id), 200
		except Exception as e:
			return jsonify({'error': str(e)}), 400
	else:
		print('Unhandled event type {}'.format(event['type']))

	return jsonify(success=True), 400

def authenticate_user(request, db, ProfileDatum):
	"""Authenticates a user based on their WhatsApp number."""
	#TODO(toni) May want to give an option to authenticate in email address.

	# Get the inputs.
	message_body = request.json
	# User number with the 'whatsapp:' prefix.
	user_number = message_body['user_number']

	# Check if there is already an entry for this person's number:
	record = db.session.query(ProfileDatum).filter(ProfileDatum.user_number == user_number).all()

	if not record:
		return jsonify(has_account=False, is_active=False, status=None), 200

	if record:
		status = record[-1].status
		logging.info('Stats: %s', status)
		if status == Status.ACTIVE.value:
			return jsonify(has_account=True, is_active=True, status=status), 200
		else:
			return jsonify(has_account=True, is_active=False, status=status), 200

	return jsonify(message='Error'), 400


def why_not_buy_save_data(request, db, WhyNotBuy):
	"""Saves reasons people are not ready to buy."""
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
		now = datetime.datetime.now()
		message_body['time'] = now

		datum = WhyNotBuy(**message_body)
		db.session.add(datum)
		db.session.commit()
		return jsonify({'message': f'Flow data saved.'}), 200

	except Exception as e:
		logging.error('error: %s', str(e))
		return jsonify({'error': str(e)}), 400






