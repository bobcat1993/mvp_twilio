import requests, json
from dotenv import load_dotenv
import os

load_dotenv()

_TEST_URL = 'https://pub-cdn.apitemplate.io/2023/08/df8bbe6c-dd4c-4fe6-91e9-e37eb78fd2ad.png'

def template_api(text: str):
		api_key = os.getenv("TEMPLATE_API_KEY")
		template_id = "c0577b23a3928f54"

		data = {
			"overrides":[
					{
						"name":"text_1",
						"text": text,
						"textBackgroundColor":"rgba(246, 243, 243, 0)"
					},
					{
						"name":"image_1",
						"src":"https://via.placeholder.com/150"
					}
			]
		}

		response = requests.post(
				F"https://rest.apitemplate.io/v2/create-image?template_id={template_id}",
				headers = {"X-API-KEY": F"{api_key}"},
				json= data
		)

		response = response.json()
		image = response['download_url_png']

		return image

def dynapictures_api(text: str):
		api_key = os.getenv("DYNAPICTURES_API_KEY")
		template_id = "1c1ea4f8a6"

		data = {
		"format": "jpeg",
		"metadata": "some text",
		"params": [
			{
				"name": "bubble",
				"imageUrl": "https://dynapictures.com/b/rest/public/media/f5ba942450/images/568b337221.png"
			},
			{
				"name": "quotes",
				"imageUrl": "https://dynapictures.com/b/rest/public/media/f5ba942450/images/779f8b9041.png"
			},
			{
				"name": "text",
				"text": text
			},
			{
				"name": "avatar",
				"imageUrl": "https://dynapictures.com/b/rest/public/media/f5ba942450/images/01c03fc023.png"
			},
			{
				"name": "name",
				"text": "bobby-chat.com"
			},
			{
				"name": "title",
				"text": "#BobbyGratitudeChallenge"
			}
			]
		}

		response = requests.post(
				F"https://api.dynapictures.com/designs/{template_id}",
				headers = {"Authorization": f"Bearer {api_key}"},
				json= data
		)

		response = response.json()
		print(response)
		image = response['imageUrl']
		return image

if __name__ == "__main__":
		url = dynapictures_api('I\'m grateful for coffee')
		print(url)

