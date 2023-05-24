import unittest
import utils
from parameterized import parameterized
import logging
from abc_types import Sentiment


class UtilsTest(unittest.TestCase):

	def test_dummy_call_api(self):

		response = utils.dummy_call_api(
			origin='test_dummy_call_api',
			out_dir='data/gpt_outputs/tests')
		self.assertIsNotNone(response)

	@parameterized.expand([
		("<tag> and </tag>", "tag", "and"),
		("<tag1> and </tag1>\n<tag2> another </tag2>",
			"tag2", "another"),
		("<tag1> and </tag1>\n<tag2> another </tag1>",
			"tag2", None),
		])
	def test_post_process_tags(self, text, tag, expected):

		output = utils.post_process_tags(text, tag)
		self.assertEqual(output, expected)




if __name__ == '__main__':
    unittest.main()
