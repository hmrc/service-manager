import contextlib
import io
from unittest.mock import Mock, patch
import unittest
from hamcrest import *

from servicemanager.smdownload import _report_hook

mock_time = Mock()
mock_time.return_value = 1000


class TestSmDownload(unittest.TestCase):
    @patch("servicemanager.smdownload._current_milli_time", mock_time)
    def test_reporthook10percent(self):
        mock_time.return_value = 1000
        f = io.StringIO()
        global offset, start
        offset = 1000
        with contextlib.redirect_stdout(f):
            _report_hook(1, 1024 * 1024, 1024 * 1024 * 10, 0, 0)
        assert_that(f.getvalue(), contains_string("10%, 1 MB, 1024 KB/s, 1 seconds passed"))

    @patch("servicemanager.smdownload._current_milli_time", mock_time)
    def test_reporthook20percent(self):
        mock_time.return_value = 4000
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            _report_hook(2, 1024 * 1024, 1024 * 1024 * 10, 0, 0)
        assert_that(f.getvalue(), contains_string("20%, 2 MB, 512 KB/s, 4 seconds passed"))
