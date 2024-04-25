# Twilio Flows

This folder contains the Twilio flows used to control the flow of the user-bot conversation.

## What is a Twilio Flow?

Check out the Twilio user guided [here](https://www.twilio.com/docs/studio/user-guide).

## How do I use these flows?

Simply create a new flow from a json as shown [here](https://www.twilio.com/docs/studio/user-guide#importing-flow-data).

## There are quite a lot of flows, what's going on?

Each feature has it's own flow and is connected to the main flow, MVP-v0.15. You can only connect a phone number to one flow at a time. If you want to test out a single feature you can connect import that feature into twilio and connect it to one of your twilio numbers, [here](https://www.twilio.com/docs/conversations/connect-to-studio).

We connect each feature to the main flow, MVP-v0.15, via the "Run Subflow" widget. These point to subflows based on their name and revision, so make sure when you are importing each feature flow into Twilio that the flow names are the same.

## What about all the Make HTTP Request widgets, what is the request URL?

TODO(tonicreswell) Update this once I've writen the secion on how to launch the app via Heroku / ngrock.

You will need to lauch the app *publicly* so that Twilio can see it at YOUR_SERVER_PATH. Then make sure that the "server_path" in the flow variables is set to YOUR_SERVER_PATH.

## Feature Subflows

TODO(tonicreswell) Explain the interactions between Google Cloud Storage, Twilio (WhatsApp), Stripe, the API (which can be hosted on ngrok for testing or Heroku for launch), and the database.

### Welcome_Flow-v0.2

The welcome feature, which welcomes new users to the app and talks them through the features available.

Note: This feature requires several assets that were stored on google cloud storage, but are not publicly accessible. 

TODO(tonicreswell) Include these assets (videos and images) in the github repo and give instructions to update the links in the Twilio flow.

### Burnout-Survey-v0

A quiz based on the [Burnout Assessment Tool](https://burnoutassessmenttool.be/wp-content/uploads/2020/08/User-Manual-BAT-version-2.0.pdf) to help individuals understand their risk of burnout.

At the end of the survey the user is presented with an infographic

### Reflect-Flow-v0.2

### Sphere-of-Influence-Flow-v0.1

### Journaling-Flow-v0.6

The interactive journaling feature. Users can either journal by topic or free style. If the user chooses to journal by topic, Bobby will help them choose a topic. Bobby helps the user explore their thoughts and feelings by asking thoughtful follow up questions.

Note: The `server_path` varible in the `server_var` widget needs to be set to YOUR_SERVER_PATH.

TIP: It's very quick and easy to get started with Free-Style journaling and most people prefer to journal about what's on their mind today rather then being confined to a specific topic series. That being said, it can also be hard to get started, so topics can server as a great starting point for individuals. Bobby's follow up questions can help individuals to explore their thoughts. User's can also say "I don't know" and Bobby will reframe the question.

### Custom-Reminders_Flow-v0.1

Allow users to set their own pace with custom reminders. Users can choose to set a reminder in 1-7 days. At their chosen time they will be sent a reminder via WhatsApp.

TIP: We've seen that invidiuals are far more likely to respond to reminders when they have autonomy over their own reminder schedule -- some people also just don't need a reminder.
