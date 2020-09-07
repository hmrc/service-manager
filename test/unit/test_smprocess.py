import unittest
import re
from hamcrest import *
from servicemanager.smprocess import SmProcess


class TestSmProcess(unittest.TestCase):

    def test_whole_arg_string_is_matched(self):
        args = ["foo", "bar", "baz"]
        assert_that(
          SmProcess.find_in_command_line(args, re.compile("foo bar")), is_(True)
        )

    def test_single_arg_is_matched(self):
        args = ["foo", "bar", "baz"]
        assert_that(
          SmProcess.find_in_command_line(args, re.compile("\\war")), is_(True)
        )
