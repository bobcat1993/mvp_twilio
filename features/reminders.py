"""Functions for sending scheduled reminders to users."""

from twilio.rest import Client
from dotenv import load_dotenv
import os
from urllib.request import urlopen
import json
import requests
from twilio.request_validator import RequestValidator
from datetime import datetime, date
from sqlalchemy import and_
from hashlib import md5
from flask import jsonify
from absl import logging

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
whatsapp_from = os.environ['WHATSAPP_NUMBER']
print(f"from: {whatsapp_from}")

# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()

def _clean_user_number(user_number):
	"""Converts from From (+44) 7479812734 to  whatsapp:+447479812734"""
	user_number = user_number.replace('(', '')
	user_number = user_number.replace(')', '')
	code, number = user_number.split(' ')
	if number.startswith('0'):
		number = number.lstrip('0')
	return f'whatsapp:{code}{number}'


def reminder(request, db, UserDatum):
	
	message_body = request.json['data']
	print(message_body)
	user_number = message_body['phone']
	message = message_body['message']

	user_number = _clean_user_number(user_number)
	user_id = string_hash(user_number)


	# Check if the user has already had a conversation today.
	today_date = date.today()
	today_rows = db.session.query(UserDatum).filter(and_(
		UserDatum.time >= today_date, UserDatum.user_number == user_id)
	).all()

	whatsapp_from = os.environ['WHATSAPP_NUMBER']

	if len(today_rows) > 0:
		return jsonify(
			message='No message sent.')
	else:
		client = Client(account_sid, auth_token)
		message = client.messages.create(
			from_=f"whatsapp:{whatsapp_from}",
			body=message,
			to=user_number,
		)
		logging.info('Reminder message stats:', message)
		return jsonify(
			message=f'Message sent to {user_number}.')
	return jsonify(message='error')

