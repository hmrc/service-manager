from unittest.mock import *

import unittest
from hamcrest import *

from servicemanager.smstatus import dostatus
from servicemanager.service.smservice import SmServiceStatus


class TestSmStatus(unittest.TestCase):
    def split_lines(self, lines):
        return [split_line for line in lines for split_line in line.split("\n")]

    def mock_service(self, service_name, up):
        mock_service = Mock()
        mock_service.service_name = service_name
        mock_service.status = (
            lambda all_process: [
                SmServiceStatus(
                    service_name,
                    123,
                    1,
                    123123,
                    512,
                    8080,
                    "",
                    "run-test-service " + service_name,
                    "",
                    SmServiceStatus.HEALTHCHECK_PASS,
                )
            ]
            if up
            else None
        )
        return mock_service

    def setUp(self):
        self.context = MagicMock()
        self.context.services = lambda: [
            self.mock_service("test-service", True),
            self.mock_service("test-service-2", False),
        ]

    def test_do_status_includes_header(self):
        result = self.split_lines(dostatus(self.context, False))
        assert_that(result, has_item("Running:"))
        assert_that(
            result, has_item(all_of(contains_string("name"), contains_string("healthcheck"))),
        )

    def test_down_service_appears_in_down(self):
        result = self.split_lines(dostatus(self.context, True))
        assert_that(result, has_item("Down:"))
        assert_that(
            result, has_item(all_of(contains_string("test-service-2"), contains_string("DOWN"))),
        )

    def test_all_processes_only_called_once(self):
        self.all_processes_called_count = 0

        def all_processes():
            self.all_processes_called_count += 1

        self.context.process_manager.all_processes = all_processes
        self.split_lines(dostatus(self.context, True))
        assert_that(self.all_processes_called_count, is_(1))
