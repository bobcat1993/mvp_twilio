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

**Apologies in advanced** Since Bobby interacts with many other external API's and micro-services (e.g. Stripe, EmailOctopus etc) it's

**Bypass Stripe Authentication (Recommended)** In `strip_payement.py` > `authenticate_user` change this to return `jsonify(has_account=True, is_active=True, status=Status.ACTIVE.value), 200`. Alternatively, you can bypass the authentication in Twilio Studio (see the image below).

![Bypass the user authentication](bypass_authentication.png)

## Further Reading

### Is this a medical device?

### Why did you use WhatsApp?

### Design principles; why not just converse with a single language model?





