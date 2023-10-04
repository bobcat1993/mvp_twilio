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

sys.path.append('..')
import utils

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

whatsapp_from = os.environ['WHATSAPP_NUMBER']


# _ASK_DAY_OF_REMINDER_SYSTEM_PROMPT = """The user will tell you when to schedule their next session. Given that today is {weekday_today} give that day of the week as "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" or "Sunday". Do not show any working, just return the string."""

# _ASSISTANT_ASKS_FOR_DAY = """When you would like to schedule your next session?"""

# _WEEKDAYS = {
# 	0: 'Monday',
# 	1: 'Tuesday',
# 	2: 'Wednesday',
# 	3: 'Thursday',
# 	4: 'Friday',
# 	5: 'Saturday',
# 	6: 'Sunday',
# 	}

# _REVERSE_WEEKDAYS = {v: k for k, v in _WEEKDAYS.items()}

def send_message(user_number):

	body = """Hi, you asked me to remind you to chat with Bobby today. I'm here whenever you are ready."""

	print("\nUSER_NUMBER:", user_number)

	message = client.messages.create(
		from_=f'whatsapp:{whatsapp_from}',
		status_callback='https://95c2-31-48-55-232.ngrok-free.app/MessageSatus',
		body=body,
		to=user_number,
	)
	return message


# def set_custom_reminder(request, scheduler):

# 	# Get the inputs.
# 	message_body = request.json

# 	# Get the list of results.
# 	user_weekday = message_body['user_weekday']
# 	user_number = message_body['user_number']

# 	# Add today's date into the system prompt.
# 	weekday_today_idx = datetime.now().weekday()
# 	weekday_today = _WEEKDAYS[weekday_today_idx]
# 	system_prompt = _ASK_DAY_OF_REMINDER_SYSTEM_PROMPT.format(weekday_today=weekday_today)

# 	messages = [
# 	{"role": "system", "content": system_prompt},
# 	{"role": "assistant", "content": _ASSISTANT_ASKS_FOR_DAY},
# 	{"role": "user", "content": user_weekday},
# 	]

# 	model_output = utils.chat_completion(
# 		model="gpt-3.5-turbo-0613",
# 		messages=messages,
# 		max_tokens=8,
# 		temperature=0.0,
# 		)

# 	user_weekday = model_output['choices'][0]['message']['content']

# 	if user_weekday.capitalize() in _REVERSE_WEEKDAYS:
# 		print("user_weekday:", user_weekday.capitalize())
# 		user_weekday_idx = _REVERSE_WEEKDAYS[user_weekday.capitalize()]

# 		if user_weekday_idx > weekday_today_idx:
# 			# If the reminder is for another day this week:
# 			trigger_days_from_now = (user_weekday_idx - weekday_today_idx)
# 		else:
# 			# If the reminder is for new week:
# 			trigger_days_from_now = (user_weekday_idx - weekday_today_idx) + 7

# 		trigger_date = datetime.now() + timedelta(days=trigger_days_from_now)

# 		# Create a DateTrigger for the specified date and time
# 		trigger = DateTrigger(run_date=job_date)

# 		# Add the job to the scheduler using the DateTrigger
# 		scheduler.add_job(my_one_time_job, trigger=trigger)


def set_custom_reminder(request, scheduler):
	"""More simple reminder what expects the user to give a number of days."""

	# Get the inputs.
	message_body = request.json

	# Get the list of results.
	user_number_of_days = message_body['user_number_of_days']
	user_number = message_body['user_number']

	# Note to self: for early testing make days minutes.
	trigger_date = datetime.now() + timedelta(minutes=float(user_number_of_days))

	# Create a DateTrigger for the specified date and time
	trigger = DateTrigger(run_date=trigger_date)

	# Add the job to the scheduler using the DateTrigger
	scheduler.add_job(send_message, args=(user_number,), trigger=trigger)

	return f'Custom reminder set for {trigger_date}.'



# day = 'monday'
# time = '22:30'
# time_zone = 

# def days_from_now(days):
# 	if (days > 0 and days <= 7):
# 			return datetime.utcnow() + timedelta(days=days)
# 	else:
# 			print('Message must be scheduled more than 15 minutes and fewer than 7 days in advance.')



# GOOGLE_CAL_LINK = """https://calendar.google.com/calendar/render?action=TEMPLATE&text={text}t&details={details}&dates={year}{month}{day}T{time}00/{year}{month}{day}T{time + 1}00&recur=RRULE:FREQ%3DWEEKLY;UNTIL%3D{year+1}{month}{day}"""



# # Event title
# text = 'Check in with Bobby (link in description).'
# # Link to chat to Bobby.
# details = 'Connect to Bobby via:+https://api.whatsapp.com/send/?phone=447830379042&text=Hi+Bobby&type=phone_number'
# # Time the user wants to chat to Bobby.
# time = '17:00'
# # Day the user wants to chat to Bobby.
# day = 'monday'
# # recurrence
# recurrence = 'WEEKLY'  # or 'DAILY'.

# # We could allow users to set 3 reminders per week and choose the time, or one reminder per week.


# print(GOOGLE_CAL_LINK.format(text=text, details=details))

# Get the current datetime as a string to feed to LLM as ref. for today.
# now = datetime.now()
# day = str(now.date())  # YYYY-MM-DD
# time = f'{now.hour}:{now.minute}'
# now = f'{day} {time}'


# # Only want to run the above once!
# message_service_id = 'MG0dd05ea6b7841b583ab8d81c096f2b08'

# body = """Hi, ready to check-in? I'm here to help with whatever is on your mind. Just say "Hi" to start a conversation with Bobby."""

# # TODO(toni) This will be running on a server in Europe... so may not get the right time-zone! Need to set time-zone!
# chosen_date = '2023-09-29 11:11'  # This will come from LLM.
# date_format = '%Y-%m-%d %H:%M'
# send_at = datetime.strptime(chosen_date, date_format).astimezone()



# message = client.messages \
# 		.create(
# 				 body=body,
# 				 # messaging_service_sid=message_service_id,
# 				 send_at=send_at,
# 				 schedule_type='fixed',
# 				 to=_TO,
# 				 from_=_FROM,
# 				 status_callback='https://95c2-31-48-55-232.ngrok-free.app/MessageSatus',
# 		 )

# print(message.sid)
# import pprint
# pprint.pprint(message)