import unittest

import p99


class Test_p99(unittest.TestCase):

    def test_version(self):

        self.assertEqual('0.0.0', p99.__version__)
