"""A one-off script to move numbers from Twilio to a db."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import os
from dotenv import load_dotenv
import csv
from absl import logging

load_dotenv()

# Create the extension
db = SQLAlchemy()

# Create a flask app (need to call db in an app context).
app = Flask(__name__)


# Connect to the PostgreSQL database on Heroku.
# Note: if you want to test this with a local db switch to
# DATABASE_URL.
database_url = os.getenv("PQSL_DATABSE_URI")
if database_url.startswith('postgres://'):
	database_url = database_url.replace(
		'postgres://', 'postgresql://', 1)
app.logger.info(database_url)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url


class ProfileDatum(db.Model):
	"""A user profile."""
	id = db.Column(db.Integer, primary_key=True)
	user_number = db.Column(db.String, nullable=True)
	user_email = db.Column(db.String, nullable=True)
	expiry_date = db.Column(db.Integer, nullable=True)
	user_wix_id = db.Column(db.String, nullable=True)


def main():

	# Load the csv.
	file = open('data/beta_testers.csv')
	csv_reader = csv.reader(file, delimiter=',')
	header = next(csv_reader)

	# Get the idx of Phone and email.
	phone_idx = header.index('Phone: must start with +')  # Phone.
	email_idx = header.index('Укажите эл. почту*')        # Email.
	id_idx = header.index('ID')        # Unique user ID from Wix.

	# Initialize the app with the extension
	db.init_app(app)

	# Create the database.
	with app.app_context():
		db.create_all()

	# Establish a connection to the PostgreSQL database
	conn = psycopg2.connect(
    host=os.getenv("PSQL_HOST"),
    database=os.getenv("PSQL_DATABASE"),
    user=os.getenv("PSQL_USER"),
    password=os.getenv("PSQL_PASSWORD"),
	)

	# Create a cursor.
	cursor = conn.cursor()

	# Iterate through the whitelist:
	for i, row in enumerate(csv_reader):

		# Get number and email.
		user_number = row[phone_idx]
		user_email = row[email_idx]
		user_wix_id = row[id_idx]

		# Post-process the user number.
		if user_number:
			# Only add data if the user has provided a number

			# From (+44) 7479812734 -->   whatsapp:+447479812734
			user_number = user_number.replace('(', '')
			user_number = user_number.replace(')', '')
			user_number = user_number.replace(' ', '')
			user_number = f'whatsapp:{user_number}'

			# The data: giving everyone 30 tokens.
			data = dict(
				user_number=user_number,
				user_email=user_email,
				user_wix_id=user_wix_id,
				expiry_date=None,
				)

			# Check if the data is already in the db.
			query = 'select * from profile_datum where user_email = %s'
			cursor.execute(query, (user_email,))
			record = cursor.fetchone()

			if not record:
				# If this user does not already have an email address in the
				# db add their information.
				with app.app_context():
					# Save the data.
					user_profile = ProfileDatum(**data)
					db.session.add(user_profile)
					db.session.commit()
			else:
				# If this user does already exist update the email.
				# Update single record.
				query = (
					'update profile_datum set user_number = %s where'
					' user_email = %s')
				cursor.execute(query, (user_number, user_email))
				conn.commit()

		else:
			logging.warn(
				f'%s has not provided a valid phone number.', user_email)

if __name__ == "__main__":
	main()