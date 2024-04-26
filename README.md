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

#### 2. Launch the app using Ngrok (for testing and personal use only).

You can launch the app using [Ngrok](https://ngrok.com/docs/getting-started/) or Heroku or any other service. Ngrok is perfect for testing and personal use.

Launch the app (from inside the **twilio** folder):
`$ python3 app.py`

Launch the app on the internet:
`ngrok http 8000`

#### 3. Setup your database.


#### 4. Setup your .env file.


#### 5. Initiate in an interaction.


#### Final details 

**Bypass Stripe Authentication (Recommended)** You can bypass the user authentication in the MVP0-v0.15 Flow in Twilio Studio by directly connecting `eval_trigger_before_authentication [No Condition Matches]` to `eval_trigger` (see the image below).

![Bypass the user authentication](bypass_authentication.png)

## Further Reading

### Is this a medical device?

### Why did you use WhatsApp?

### Design principles; why not just converse with a single language model?

### Why are some tests commented out?

These tests use LLMs which means that running them all can be expensive.





