"""Functions to allow users to set custom reminders.

Link to messages that have been scheduled: https://console.twilio.com/us1/develop/sms/overview
"""

import os
from twilio.rest import Client
from datetime import datetime, timedelta
from apscheduler.triggers.date import DateTrigger
from dotenv import load_dotenv
import time
import sys
from absl import logging
from flask import jsonify
from hashlib import md5

sys.path.append('..')
import utils

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

whatsapp_from = os.environ['WHATSAPP_NUMBER']

# TODO(toni) Move to utils.
def string_hash(string):
	return md5(string.encode()).hexdigest()

def get_CustomReminderDatum(db):
	class CustomReminderDatum(db.Model):
		"""Stores the data from the Custom Reminder Flow."""

		id = db.Column(db.Integer, primary_key=True)
		is_reminder_set = db.Column(db.String, nullable=True)
		why_not_set_reminder = db.Column(db.String, nullable=True)
		user_number_of_days = db.Column(db.String, nullable=True)
		flow_sid = db.Column(db.String, nullable=True)
		origin = db.Column(db.String, nullable=True)
		user_id = db.Column(db.String, nullable=True)
		error = db.Column(db.String, nullable=True)
		time = db.Column(db.DateTime, nullable=True)

	return CustomReminderDatum

def send_message(user_number):

	body = """Hi, you asked me to remind you to chat with Bobby today. I'm here whenever you are ready."""

	print("\nUSER_NUMBER:", user_number)

	message = client.messages.create(
		from_=f'whatsapp:{whatsapp_from}',
		status_callback='https://8747-81-103-170-52.ngrok-free.app/MessageSatus',
		body=body,
		to=user_number,
	)
	return message

def set_custom_reminder(request, scheduler):
	"""More simple reminder what expects the user to give a number of days."""

	# Get the inputs.
	message_body = request.json

	# Get the list of results.
	user_number_of_days = message_body['user_number_of_days']
	user_number = message_body['user_number']

	# Note to self: for early testing make days minutes.
	trigger_date = datetime.now() + timedelta(days=float(user_number_of_days))

	# Create a DateTrigger for the specified date and time
	trigger = DateTrigger(run_date=trigger_date)

	# Add the job to the scheduler using the DateTrigger
	scheduler.add_job(func=send_message,
	                  args=(user_number,),
	                  trigger=trigger,
	                  misfire_grace_time=None)

	return jsonify({
	  'message': f'Custom reminder set for {trigger_date}.'}), 200


def save_data(request, db, CustomReminderDatum):
	"""Saves data from the custom reminder flow."""
	# Retrieve data from the request sent by Twilio
	try:
		message_body = request.json

		# Hash the user_id so that the data is pseudo-anonyms.
		message_body['user_id'] = string_hash(message_body['user_id'])

		# Get the current time.
		now = datetime.now()
		message_body['time'] = now

		datum = CustomReminderDatum(**message_body)
		db.session.add(datum)
		db.session.commit()

		return jsonify({'message': f'Flow data saved.'}), 200
	except Exception as e:
		logging.error('error: %s', str(e))
		return jsonify({'error': str(e)}), 400