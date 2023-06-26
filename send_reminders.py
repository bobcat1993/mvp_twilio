from twilio.rest import Client
from dotenv import load_dotenv
import os
from urllib.request import urlopen
import json
import requests
from twilio.request_validator import RequestValidator

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

white_list = response.json()

# Get the person running the script to confirm they want to run this:
input(f"This will send a message to {len(white_list)} contacts."
			" Press enter to continue...")

for number in white_list:
	print(f'Sending message to {number}.')

	client = Client(account_sid, auth_token)

	message = client.messages.create(
		from_=f"whatsapp:{whatsapp_from}",
		body=('Hi! It\'s Bobby here, ready for a check in? Just say "Hi"'
					' when you are ready to start.'),
		to=number,
	)

	print("message:", message)