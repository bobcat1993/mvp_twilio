from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Replace with your Twilio Account SID and Auth Token
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

# Replace with the Conversation SID you want to delete
conversation_sid = 'CH66b19b129bd74dc29f6b164fb072c4ad'

client = Client(account_sid, auth_token)

try:
    conversation = client.conversations.conversations(conversation_sid).delete()
    print(f"Conversation SID {conversation_sid} successfully deleted.")
except Exception as e:
    print(f"Error deleting conversation: {e}")