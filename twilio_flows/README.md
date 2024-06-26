# Twilio Flows

This folder contains the Twilio flows used to control the flow of the user-bot conversation.

## What is a Twilio Flow?

Check out the Twilio Studio user guided [here](https://www.twilio.com/docs/studio/user-guide).

[This short tutorial](https://www.twilio.com/docs/studio/tutorials/customer-support-menu) is also great for understanding how to use Twilio Studio with WhatsApp.

## How do I use these flows?

Simply create a new flow from a json as shown [here](https://www.twilio.com/docs/studio/user-guide#importing-flow-data) and connect to your Twilio WhatsApp senders as shown [here](https://www.twilio.com/docs/studio/tutorials/customer-support-menu#connect-your-whatsapp-sender-to-your-studio-flow).

## There are quite a lot of flows, what's going on?

Each feature has it's own flow and is connected to the main flow, MVP-v0.15. You can only connect a WhatsApp number to one flow at a time. If you want to test out a single feature you can import that feature into Twilio and connect it to one of your Twilio WhatsApp senders, [here](https://www.twilio.com/docs/studio/tutorials/customer-support-menu).

We connect each feature to the main flow, MVP-v0.15, via the "Run Subflow" widget. These point to subflows based on their name and revision, so make sure when you are importing each feature flow into Twilio that the flow names are the same.

## What about all the Make HTTP Request widgets, what is the request URL?

TODO(tonicreswell) Update this once I've written the section on how to launch the app via Heroku / ngrok.

You will need to launch the app *publicly* so that Twilio can see it at YOUR_SERVER_PATH. Then make sure that the "server_path" in the flow variables is set to YOUR_SERVER_PATH.

## Feature Subflows

TODO(tonicreswell) Explain the interactions between Google Cloud Storage, Twilio (WhatsApp), Stripe, the API (which can be hosted on ngrok for testing or Heroku for launch), and the database.

TODO(tonicreswell) The building philosophy: merging traditional conversation design (e.g. Siri) with language models to implement therapeutic and coaching techniques.

### Welcome_Flow-v0.2

The welcome feature, which welcomes new users to the app and talks them through the features available.

Note: This feature requires several assets that were stored on google cloud storage, but are not publicly accessible. 

TODO(tonicreswell) Include these assets (videos and images) in the github repo and give instructions to update the links in the Twilio flow.

### Burnout-Survey-v0

A quiz based on the [Burnout Assessment Tool](https://burnoutassessmenttool.be/wp-content/uploads/2020/08/User-Manual-BAT-version-2.0.pdf) to help individuals understand their risk of burnout.

Note: At the end of the survey the user is presented with an infographic this currently requires you to have a Google Cloud Storage (GCS) account setup as well as the API. However, the steps interacting with the API and GCS can be skipped when running the flow, Twilio.

### Reflect-Flow-v0.2

Inspired by the ABC (Activating event, Behaviour, Consequences) of Cognitive Behavioural Therapy (CBT) this flow was designed to help people challenge negative thought patterns.

TIP: This was the first feature we built and has been through many iterations. This is also a great stand alone feature to test in Twilio.

Note: We built channels for feedback directly into the conversation, significantly reducing friction for our users and maximising the real-time feedback we were getting. The data we collected gave us a gauge for what was working/ not working and helped us understand how outcomes related to engagement.

Note: The `ngrok_path` variable in the `set_variables_1` widget needs to be set to YOUR_SERVER_PATH.


### Sphere-of-Influence-Flow-v0.1

Sphere of Influence is a technique often used by coaches to help individuals navigate situations where they feel a lack of control. This features guides users towards letting go of things that are outside of their control and re-focus their energy on what they can control.

Note: While this technique has two clear stages, first identifying what's outside of an individuals control then identifying what they can control. Efforts to split this process in two -- prompting two different language models -- lead to challenges because language models were not able to reliably identifying when users had finished with each stage.

Note: The `server_path` variable in the `server_var` widget needs to be set to YOUR_SERVER_PATH.


### Journaling-Flow-v0.6

The interactive journaling feature. Users can either journal by topic or free style. If the user chooses to journal by topic, Bobby will help them choose a topic. Bobby helps the user explore their thoughts and feelings by asking thoughtful follow up questions.

Note: The `server_path` variable in the `server_var` widget needs to be set to YOUR_SERVER_PATH.

TIP: It's very quick and easy to get started with Free-Style journaling and most people prefer to journal about what's on their mind today rather then being confined to a specific topic series. That being said, it can also be hard to get started, so topics can server as a great starting point for individuals. Bobby's follow up questions can help individuals to explore their thoughts. User's can also say "I don't know" and Bobby will reframe the question.

### Custom-Reminders_Flow-v0.1

Allow users to set their own pace with custom reminders. Users can choose to set a reminder in 1-7 days. At their chosen time they will be sent a reminder via WhatsApp.

TIP: We've seen that individuals are far more likely to respond to reminders when they have autonomy over their own reminder schedule -- some people also just don't need a reminder.

### Where are the rest of the flows?

Thought Bobby's (short) life, we built and tested many different features, not all of them made the cut. In the code base you will see some features that did not make the cut. For example, our boundaries and gratitude challenges.



