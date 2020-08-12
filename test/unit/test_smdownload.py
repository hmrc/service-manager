import contextlib
import io
import unittest.mock

from hamcrest import *

from servicemanager.smdownload import _report_hook, _current_milli_time


class TestSmDownload(unittest.TestCase):


    def test_reporthook10percent(self):
        f = io.StringIO()
        start = _current_milli_time() - 1000
        with contextlib.redirect_stdout(f):
            _report_hook(1, 1024*1024, 1024*1024*10, start, start)
        assert_that(f.getvalue(), contains_string("10%, 1 MB, 1024 KB/s, 1 seconds passed"))

    def test_reporthook20percent(self):
        f = io.StringIO()
        start = _current_milli_time() - 4000
        with contextlib.redirect_stdout(f):
            _report_hook(2, 1024*1024, 1024*1024*10, start, start)
        assert_that(f.getvalue(), contains_string("20%, 2 MB, 512 KB/s, 4 seconds passed"))
