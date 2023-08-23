"""Functions for tracking users progress."""

from twilio.rest import Client
from dotenv import load_dotenv
import os
from urllib.request import urlopen
import json
import requests
from twilio.request_validator import RequestValidator
from datetime import datetime, date, timedelta
from sqlalchemy import and_
from hashlib import md5
from flask import jsonify
from absl import logging

load_dotenv()

# The max. number of visits that get rewarded each week.
_MAX_STRIKE_VALUE = 3

_STRIKE_IMAGE_LINK = """https://storage.googleapis.com/bobby-chat-goals/day_{day}_of_3.jpeg"""

# TODO(toni) Update this image and the test.
_BACKUP_STRIKE_IMAGE_LINK = """https://storage.googleapis.com/bobby-chat-goals/daydefault_of_7.png"""

# TODO(toni) Add this to a utils.py file.
def string_hash(string):
	return md5(string.encode()).hexdigest()

def get_number_of_visits(db, user_number, UserDatum):
	"""Returns the number if visits this week."""

	# Calculate the start and end of the current week
	today = datetime.now()
	# Today minus the day of the week number.
	start_of_week = today - timedelta(days=today.weekday())
	end_of_week = start_of_week + timedelta(days=6)


	# TODO(toni) Only count one visit per day. Right now it counts multiple per day.
	logging.info('start date: %s, end date: %s', str(start_of_week), str(end_of_week))
	visits_this_week = db.session.query(UserDatum).filter(
		and_(
			UserDatum.time >= start_of_week,
			UserDatum.time <= end_of_week,
			UserDatum.user_number == user_number
			)
	).all()

	logging.info('visits_this_week:  %s', visits_this_week)
	for visit in visits_this_week:
		logging.info(visit)

	return len(visits_this_week)


def get_streak_infographic(request, db, UserDatum):
	"""Returns a graphic based on number of user visits this week."""

	user_number = request.json['user_number']
	user_number = string_hash(user_number)

	number_of_visits = get_number_of_visits(db, user_number, UserDatum)

	# The number of visits should never be less than one since this should only be used after a user has had an interaction.
	if number_of_visits < 1:
		# raise ValueError('number of visits is %s which is less than 1.', str(number_of_visits))
		logging.warning('number of visits is %s which is less than 1.', str(number_of_visits))
		number_of_visits = 1

	if number_of_visits < _MAX_STRIKE_VALUE:
		image_url = _STRIKE_IMAGE_LINK.format(day=number_of_visits)
	else:
		image_url = _BACKUP_STRIKE_IMAGE_LINK

	logging.info(image_url)
	return jsonify(image_url=image_url)






