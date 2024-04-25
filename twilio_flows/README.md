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

You will need to lauch the app *publicly* so that Twilio can see it. Then make sure that the "server_path" in the flow variables is set to that path.

## Subflows

### Welcome_Flow-v0.2

### Burnout-Survey-v0

### Reflect-Flow-v0.2

### Sphere-of-Influence-Flow-v0.1

### Journaling-Flow-v0.6

The interactive journaling feature. Users can either journal by topic or free style. If the user chooses to journal by topic, Bobby will help them choose a topic. Bobby helps the user explore their thoughts and feelings by asking thoughtful follow up questions.

### Custom-Reminders_Flow-v0.1

  
