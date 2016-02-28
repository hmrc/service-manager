from servicemanager.server import smserverlogic
from servicemanager.server.smserverlogic import BadRequestException
from servicemanager.service.smplayservice import SmPlayService
from servicemanager.smcontext import SmApplication
from servicemanager.smprocess import SmProcess

import time
import pytest

from testbase import TestBase

class TestServerFunctionality(TestBase):

    def test_simple(self):
        context = self.createContext()
        self.startFakeNexus()

        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                               {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                               {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()

        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        self.assertIsNotNone(context.get_service("DROPWIZARD_NEXUS_END_TO_END_TEST").status())
        self.assertIsNotNone(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status())
        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything(True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])
        self.assertEqual(context.get_service("DROPWIZARD_NEXUS_END_TO_END_TEST").status(), [])
        self.assertEqual(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status(), [])

    def test_play_with_append_args(self):
        context = self.createContext()
        self.startFakeNexus()

        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT", "appendArgs": ["-Dfoo=bar"]}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()

        self.waitForCondition(lambda : len(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status()), 1)

        service = SmPlayService(context, "PLAY_NEXUS_END_TO_END_TEST")
        processes = SmProcess.processes_matching(service.pattern)
        self.assertEqual(len(processes), 1)
        self.assertTrue("-Dfoo=bar" in processes[0].args)

        context.kill_everything(True)
        self.assertEqual(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status(), [])

    def test_play_with_invalid_append_args(self):
        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT", "appendArgs": "-Dshould=be-an-array"}]
        with pytest.raises(BadRequestException):
            smserverlogic.SmStartRequest(server, request, True, False).process_request()

    def test_external_with_append_args(self):
        context = self.createContext()
        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT", "appendArgs": [";echo foo"]}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        pattern = context.application.services["TEST_ONE"]["pattern"]

        self.waitForCondition(lambda : len(SmProcess.processes_matching(pattern)), 2)
        processes = SmProcess.processes_matching(pattern)
        self.assertTrue(";echo" in processes[0].args or ";echo" in processes[1].args)

        context.kill_everything(True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_external_with_invalid_append_args(self):
        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT", "appendArgs": ";echo foo"}]
        with pytest.raises(BadRequestException):
            smserverlogic.SmStartRequest(server, request, True, False).process_request()

    def test_offline(self):
        context = self.createContext()
        self.startFakeNexus()
        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                               {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                               {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything(True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])
        request["testId"] = "foo2"
        smserverlogic.SmStartRequest(server, request, True, True).process_request()

        self.waitForCondition(lambda : context.get_service("TEST_ONE").status() is not None, True)
        # stop does not currently work for extern
        #smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything(True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_ensure_multiple_instances_of_a_service_can_be_started_from_server(self):
        context = self.createContext()
        server = smserverlogic.SmServer(SmApplication(self.config_dir_override, None))
        test_services = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                         {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                         {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]

        self.startFakeNexus()

        first_request = dict()
        first_request["testId"] = "multiple-instance-unit-test-1"
        first_request["services"] = test_services
        smserverlogic.SmStartRequest(server, first_request, True, False).process_request()

        def single_service_started_successfully():
            if len(context.get_service("TEST_ONE").status()) != 1: return False
            if len(context.get_service("DROPWIZARD_NEXUS_END_TO_END_TEST").status()) != 1: return False
            if len(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status()) != 1: return False
            return True

        self.waitForCondition(single_service_started_successfully, True)

        second_request = dict()
        second_request["testId"] = "multiple-instance-unit-test-2"
        second_request["services"] = test_services
        smserverlogic.SmStartRequest(server, second_request, True, False).process_request()

        def multiple_services_started_successfully():
            if len(context.get_service("TEST_ONE").status()) != 2: return False
            if len(context.get_service("DROPWIZARD_NEXUS_END_TO_END_TEST").status()) != 2: return False
            if len(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status()) != 2: return False
            return True

        self.waitForCondition(multiple_services_started_successfully, True)

        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything(True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])