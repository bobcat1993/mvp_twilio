# Build your own well-being companion in WhatsApp

## BobbyChat

### Back story to this code.


### Overview

BobbyChat communicates with users via WhatsApp. To send and receive messages via WhatsApp, we use [Twilio Studio](https://www.twilio.com/docs/studio/user-guide). Twilio Studio allows us to design the structure of a conversation (see example image below) while executing each step of the conversation using language models (aka GenAI).

![Example conversation structure](goal_setting_demo.png).

Twilio communicates with our language models via an API which needs to be hosted publicly (so that Twilio can access the end-points). We used [Heroku](https://www.heroku.com/) (with a PostgreSQL database), and ngrok for testing and developing locally.

Our API also communicated with Stripe, Google Cloud Storage and EmailOctopus. Integrations with Stripe and EmailOctopus allowed us to put up a paywall (despite serving our app through WhatsApp), only allow signed-up users and integrate other marketing channels. These elements can be easily removed/ skipped (done easily on the Twilio Studio side). 
We decided to open source the code with these elements to help others if they decided to build a product in WhatsApp. See a high-level overview of the architecture below.

![Bobby architecture overview](bobby_architecutre_overview.png)


### What you will need

* Twilio (required)
	* A Twilio account.
	* In Twilio [configure a WhatsApp sender](https://console.twilio.com/us1/develop/sms/senders/whatsapp-senders).
	* Then you should have a:
		* [TWILIO_AUTH_TOKEN](https://console.twilio.com/)
		* [TWILIO_ACCOUNT_SID](https://console.twilio.com/)
		* WHATSAPP_NUMBER
	* Add these to a .env file ([what is a .env file?](https://medium.com/@sujathamudadla1213/what-is-the-use-of-env-8d6b3eb94843)).

* [Heroku](https://www.heroku.com/) or [Ngrok](https://ngrok.com/docs/getting-started/) account (or equivalent, required) for hosting your API on the internet so that Twilio can communicate with it.
	* The path at which your website is hosted is `YOUR_SERVER_PATH` (we will use this later).

* A PostgreSQL database (required).
	* This can either be [setup as an add-on](https://devcenter.heroku.com/articles/heroku-postgresql) in Heroku or setup [locally](https://www.postgresql.org/).
	* Then you should have a `DATABASE_URL` something similar to `postgresql:///<db_name>`. Add this to your .env file.

* ChatGPT (required).
	* An [OpenAI account](https://platform.openai.com/signup) with a `OPENAI_API_KEY` which you can find [here](https://platform.openai.com/api-keys).
	* Add `OPENAI_API_KEY` to your .env file.

* Stripe (optional and not recommended).
	* To access BobbyChat our users had to purchase a subscription via Stripe. When a purchase was complete Stripe would send a webhook to our app (https://docs.stripe.com/webhooks/quickstart) with the user's phone number and this allowed us to seamlessly authenticate paying users via their phone number. Stripe also sent webhooks when the subscription expired.
	* Add `STRIPE_API_KEY` and `STRIPE_SECRET` to your .env file.

* Google Cloud Storage (optional and not recommended).

**Important** Everything in your .env file is a secret, don't share it with anyone else (and don't accidentally commit it -- it could be an expensive mistake).


### Setup

Since Bobby interacts with many other external API's and micro-services (e.g. Stripe, EmailOctopus etc) this code will **not** run out of the box and will require some setup.

#### 1. Importing the Twilio Flows into Twilio Studio.

Once you have forked this repo, you will have a folder named `twilio_flows`. This folder holds the Twilio Flow JSONs that execute the conversation. You will need to navigate to your [Twilio Console](https://console.twilio.com/) > Studio > Flows > Create new Flow > _name the flow the same as the file name_ > Import from JSON.

You can either experiment with one flow at a time (recommended) or import them all with the main flow being MVP0-v0.15.

You will need to [connect the flow to a Twilio WhatsApp sender (phone number)](https://www.twilio.com/docs/studio/tutorials/customer-support-menu#connect-your-whatsapp-sender-to-your-studio-flow). **Be sure to connect it to a WhatsApp number (not a regular number)**.

It's recommended to start with one feature, for example, Sphere-of-Influence-Flow-v0.1 (since the flow is more simple).

#### 2. Launch the app using Ngrok (for testing and personal use only).

You can launch the app using [Ngrok](https://ngrok.com/docs/getting-started/) or Heroku or any other service. Ngrok is perfect for testing and personal use.

Launch the app (from inside the **twilio** folder):
`$ python3 app.py`

Launch the app on the internet:
`ngrok http 8000`

#### 3. Setup your PostgreSQL database (locally).

Once you had installed PostgreSQL run the following command to login to your PostgreSQL server using your username and hostname (if you have them).

`$ psql -U <username> -h <hostname>`

Create a database:

`$ CREATE DATABASE <database_name>;`


Your `DATABASE_URL` will have the form `postgresql://<username>:<password>@<hostname>:<port>/<database_name>`. You can find out this info using the `\conninfo` command.


#### 4. Setup Google Cloud Storage (not recommended).

TODO(tonicreswell) Write this section.


#### 5. Setup your .env file.

Create a .env file (inside the **twilio** folder):

`$ vim .env`

Open the file and paste the following, replacing the #### values with your own (the Google credentials are optional and only required for the Burnout Survey flow). For local testing STRIPE_SECRET should be set to None.

```
OPENAI_API_KEY=####
DATABASE_URL=postgresql:///####
TWILIO_AUTH_TOKEN=####
TWILIO_ACCOUNT_SID=####
WHATSAPP_NUMBER=+####

GOOGLE_API_KEY=####
GOOGLE_CREDENTIALS=####.json
GOOGLE_APPLICATION_CREDENTIALS=####.json

STRIPE_API_KEY=sk_test_####
STRIPE_SECRET=####
```

#### 6. Initiate in an interaction.

Make sure that you have connected one of your WhatsApp senders to one of the flows (we recommend the Sphere-of-Influence flow to get started) and send a "Hi" message via WhatsApp to that connected number. This will initiate the conversation and the magic will begin.

#### 7. Trouble Shooting

a. What is a WhatsApp sender?

For a quick-start you can use [Twilio's WhatsApp sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn) which allows you to connect to send WhatsApp messages to a small number of users. Go to the Sandbox settings to change where incoming messages are sent.

If you have set a Twilio account, you will find your WhatsApp senders [here](https://console.twilio.com/us1/develop/sms/senders/whatsapp-senders).

b. I have a WhatsApp sender why is nothing happening when I send a message?

You need to make sure that your WhatsApp sender is connected to the correct flow. Follow [these steps to setup the end point URLs](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn); it's as simple as copying a URL from one place to another.

c. I'm getting a `KeyError: 'TWILIO_ACCOUNT_SID'` when I run `$ python3 app.py`.

This means that your .env file is not configured correctly. Make sure the file is named .env and that the missing key is in the .env file.

d. I'm getting an error on the `Make HTTP Request` widgets, what is `flow.variables.server_path`?

Each flow will have a `server_path` or `ngrok_path` (or similar variable) set in the first widget of each flow. You must replace this with your Ngrok (or equivalent) path.

e. How do I find my Ngrok path?

When you run `$ ngrok http 8000` you will see something similar to `https://####-##-##-##-###.ngrok-free.app -> http://localhost:8000 `. `https://####-##-##-##-###.ngrok-free.app` is your Ngrok path.


f. I'm getting an error on the `Make HTTP Request` widgets and I've set my server path correctly?

Visit `https://####-##-##-##-###.ngrok-free.app` and you may see an error message. Ngrok also have brilliant inspectors which show you exactly where things are going wrong in the HTTP calls.




#### Final details 

**Bypass Stripe Authentication (Recommended)** You can bypass the user authentication in the MVP0-v0.15 Flow in Twilio Studio by directly connecting `eval_trigger_before_authentication [No Condition Matches]` to `eval_trigger` (see the image below).

![Bypass the user authentication](bypass_authentication.png)

## Further Reading

### Is this a medical device?

### Why did you use WhatsApp?

### Design principles; why not just converse with a single language model?

### Why are some tests commented out?

These tests use LLMs which means that running them all can be expensive.





