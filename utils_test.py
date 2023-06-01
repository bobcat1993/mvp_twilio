import unittest
import utils
from parameterized import parameterized
import logging
from abc_types import Sentiment


class UtilsTest(unittest.TestCase):

	def test_dummy_call_api(self):

		response = utils.dummy_call_api(
			origin='test_dummy_call_api',
			out_dir='data/gpt_outputs')

		self.assertIsNotNone(response)
		self.assertIsNotNone(response['choices'][0]['text'])

	def test_setup_openai(self):
		model_list = utils.setup_openai()
		logging.info(model_list)

		self.assertIsNotNone(model_list)

	def test_call_api(self):

		response = utils.call_api(
			origin='test_call_api',
			out_dir='data/gpt_outputs',
			prompt='This is a test.',
			max_tokens=1)
		self.assertIsNotNone(response)
		self.assertIsNotNone(response['choices'][0]['text'])

	@parameterized.expand([
		("<tag> and </tag>", "tag", "and"),
		("<tag1> and </tag1>\n<tag2> another </tag2>",
			"tag2", "another"),
		("<tag1> and </tag1>\n<tag2> another </tag1>",
			"tag2", None),
		("<tag> And it was FUN </tag>", "tag", "And it was FUN"),
		("<tag> And it was FUN. </tag>", "tag", "And it was FUN"),
		])
	def test_post_process_tags(self, text, tag, expected):

		output = utils.post_process_tags(text, tag)
		self.assertEqual(output, expected)

if __name__ == '__main__':
  unittest.main()
