# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

from absl import flags, app
from dotenv import load_dotenv

load_dotenv()

flags.DEFINE_string(
	'sid',
	None,
	'IGXXXXX, The SID of the Address Configuration resource. '
	'This value can be either the sid or the address of the '
	'configuration.')

FLAGS = flags.FLAGS

def main(_):
	# Find your Account SID and Auth Token at twilio.com/console
	# and set the environment variables. See http://twil.io/secure
	account_sid = os.environ['TWILIO_ACCOUNT_SID']
	auth_token = os.environ['TWILIO_AUTH_TOKEN']
	client = Client(account_sid, auth_token)

	print('sid:', FLAGS.sid)
	client.conversations.v1.address_configurations(
		FLAGS.sid) \
		.delete()

if __name__ == '__main__':
	app.run(main)