from servicemanager.actions import actions
from servicemanager.smcontext import SmApplication, SmContext, ServiceManagerException
from servicemanager.smprocess import SmProcess
from servicemanager.service.smplayservice import SmPlayService
from servicemanager.serviceresolver import ServiceResolver

import pytest

from testbase import TestBase

class TestActions(TestBase):

    def test_start_and_stop_one(self):
        context = SmContext(SmApplication(self.config_dir_override), None, False, False)
        result = actions.start_one(context, "TEST_ONE", True, False, None, port=None)
        self.assertTrue(result)

        self.waitForCondition((lambda : len(context.get_service("TEST_ONE").status())), 1)
        context.kill("TEST_ONE", True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_start_and_stop_one_with_append_args(self):
        context = SmContext(SmApplication(self.config_dir_override), None, False, False)
        actions.start_one(context, "TEST_ONE", True, False, None, None, ["; echo 'Fin du sleep!!'"])
        # Expect two in this case because the append creates a forked process
        self.waitForCondition((lambda : len(context.get_service("TEST_ONE").status())), 2)
        context.kill("TEST_ONE", True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    @pytest.mark.online
    def test_dropwizard_from_source(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        servicetostart = "DROPWIZARD_NEXUS_END_TO_END_TEST"
        actions.start_and_wait(service_resolver, context, [servicetostart], False, False, None, port=None, seconds_to_wait=90, append_args=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)
        self.assertEqual(context.get_service(servicetostart).status(), [])

    def test_dropwizard_from_jar(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        self.startFakeNexus()

        servicetostart = "DROPWIZARD_NEXUS_END_TO_END_TEST"
        actions.start_and_wait(service_resolver, context, [servicetostart], True, False, None, port=None, seconds_to_wait=90, append_args=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)
        self.assertEqual(context.get_service(servicetostart).status(), [])

    @pytest.mark.online
    def test_play_from_source(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        servicetostart = "PLAY_NEXUS_END_TO_END_TEST"
        port = None
        secondsToWait = 90
        append_args = None
        actions.start_and_wait(service_resolver, context, [servicetostart], False, False, None, port, secondsToWait, append_args)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)
        self.assertEqual(context.get_service(servicetostart).status(), [])

    def test_successful_play_from_jar_without_waiting(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        context.kill_everything(True)

        self.startFakeNexus()

        fatJar = True
        release = False
        proxy = None
        port = None
        seconds_to_wait = None
        append_args = None

        try:
            servicetostart = ["PLAY_NEXUS_END_TO_END_TEST"]
            actions.start_and_wait(service_resolver, context, servicetostart, fatJar, release, proxy, port, seconds_to_wait, append_args)
        finally:
            context.kill_everything(True)

    def test_successful_play_from_jar_without_waiting_with_append_args(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        context.kill_everything(True)

        self.startFakeNexus()

        servicetostart = ["PLAY_NEXUS_END_TO_END_TEST"]
        appendArgs = {"PLAY_NEXUS_END_TO_END_TEST": ["-DFoo=Bar"]}
        fatJar = True
        release = False
        proxy = None
        port = None
        seconds_to_wait = None

        actions.start_and_wait(service_resolver, context, servicetostart, fatJar, release, proxy, port, seconds_to_wait, appendArgs)
        service = SmPlayService(context, "PLAY_NEXUS_END_TO_END_TEST")
        self.waitForCondition(lambda : len(SmProcess.processes_matching(service.pattern)), 1)
        processes = SmProcess.processes_matching(service.pattern)
        self.assertTrue("-DFoo=Bar" in processes[0].args)

    def test_failing_play_from_jar(self):

        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        context.kill_everything(True)

        self.startFakeNexus()

        try:
            servicetostart = ["BROKEN_PLAY_PROJECT"]
            actions.start_and_wait(service_resolver, context, servicetostart, fatjar=True, release=False, proxy=None, port=None, seconds_to_wait=2, append_args=None)
            self.fail("Did not expect the project to startup.")
        except ServiceManagerException as sme:
            self.assertEqual("Timed out starting service(s): BROKEN_PLAY_PROJECT", sme.message)
        finally:
            context.kill_everything(True)


    def test_start_and_stop_one_duplicate(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        actions.start_and_wait(service_resolver, context, ["TEST_ONE"], False, False, None, port=None, seconds_to_wait=90, append_args=None)

        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        result = actions.start_one(context, "TEST_ONE", True, False, None, port=None)
        self.assertFalse(result)
        context.kill("TEST_ONE", True)
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_assets_server(self):
        context = SmContext(SmApplication(self.config_dir_override), None, False, False)
        context.kill_everything(True)

        self.startFakeNexus()

        actions.start_one(context, "PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", True, False, None, port=None)
        self.assertIsNotNone(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status())
        context.kill("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", wait=True)

        self.assertEqual(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status(), [])

    def test_wait_on_assets_server(self):
        sm_application = SmApplication(self.config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)
        context.kill_everything(True)

        self.startFakeNexus()

        port = None
        seconds_to_wait = 5
        append_args = None
        actions.start_and_wait(service_resolver, context, ["PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND"], True, False, None, port, seconds_to_wait, append_args)
        self.assertIsNotNone(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status())
        context.kill("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", True)

        self.assertEqual(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status(), [])

    def test_python_server_offline(self):
        context = SmContext(SmApplication(self.config_dir_override), None, True, False)
        port = None
        append_args = None
        actions.start_one(context, "PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", True, False, None, port, append_args)
        self.assertIsNotNone(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status())
        context.kill("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", True)
        self.assertEqual(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status(), [])
