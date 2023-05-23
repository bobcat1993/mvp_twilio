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




if __name__ == '__main__':
    unittest.main()
