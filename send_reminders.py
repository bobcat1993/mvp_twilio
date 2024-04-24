from twilio.rest import Client
from dotenv import load_dotenv
import os
from urllib.request import urlopen
import json
import requests
from twilio.request_validator import RequestValidator
from absl import logging
import time

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

#=============
# The url for the allowed phone numbers.
assets_url = os.environ['ASSETS_URL']
whatsapp_from = os.environ['WHATSAPP_NUMBER']
print(f"from: {whatsapp_from}")

	
# Create an HTTP GET request to fetch the JSON asset
validator = RequestValidator(auth_token)
signature = validator.compute_signature(assets_url, params={})
headers = {'X-Twilio-Signature': signature}
response = requests.get(assets_url, headers=headers)

# # white_list = response.json()
white_list = []


# Get the person running the script to confirm they want to run this:
input(f"This will send a message to {len(white_list)} contacts."
			" Press enter to continue...")

_BODY="""Hi, did you know that journaling can be a great way to process strong emotions -- good or bad. We've added topics to our journaling feature so you can focus on specific areas such as boundary setting, self-care and even time management. There's always an option to Journal Free Style - if you prefer. Just press "Start Journaling" to get started."""

input(f"This is the message you are about to send:\n {_BODY}"
			"\nAre you sure this is the message you would like to send?")

client = Client(account_sid, auth_token)

for number in white_list:
	print(f'Sending message to {number}.')

	# TODO(toni) Check who has not already checked in today and only 
	# message them.

	# Look at ngrok to get the delivery stats.
	message = client.messages.create(
		from_=f"whatsapp:{whatsapp_from}",
		# TODO(toni) Make this a variable to be used with a config.
		# status_callback='https://<myapp>.app/MessageSatus',
		body=_BODY,
		to=number,
	)

	print("message:", message)