"""Script to set a particular "sender" (e.g. Twilio SMS number or 
Twilio WhatsApp sender) to automatically create a new Conversation 
when it receives a message that wouldn’t be mapped to an existing 
Conversation
"""
import os
from twilio.rest import Client

from dotenv import load_dotenv

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# address = 'whatsapp:+447897009528'

# address_configurations = client.conversations \
#     .v1 \
#     .address_configurations \
#     .list()

# print(address_configurations)

# address_exists = False

# for address_configuration in address_configurations:
#     if address_configuration.address == address:
#         address_exists = True
#         break

# if address_exists:
#     print("Address configuration already exists.")
#     # You can choose to update the existing configuration here if needed.
# else:
#     print("Address configuration does not exist. You can proceed with creating the new one.")
#     # Code to create the new address configuration goes here.


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

address_configuration = client.conversations \
    .v1 \
    .address_configurations \
    .create(
         friendly_name='Connecting conversations to Studio',
         auto_creation_enabled=True,
         auto_creation_type='studio',
         auto_creation_studio_flow_sid='FW071ef6f74454b46e82ba9f5ca21dab4c',
         type='whatsapp',
         address='whatsapp:+447897009528'
     )

print(address_configuration.sid)
