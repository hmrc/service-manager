import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '../servicemanager'))

# dont do this in production code, this is bad practice it would seem, only for tests
from servicemanager.actions import actions
from servicemanager.server import smserverlogic
from servicemanager.smcontext import SmApplication, SmContext, ServiceManagerException
from servicemanager.smprocess import SmProcess
from servicemanager.service.smplayservice import SmPlayService
from servicemanager.server.smserverlogic import BadRequestException

import pytest
import time
import shutil
import unittest

from servicemanager.serviceresolver import ServiceResolver

from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from servicemanager.smcredentials import EnvNexusCredentials, CredentialsResolver, SbtNexusCredentials

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def set_up_and_clean_workspace():
    workspace_dir = os.path.join(os.path.dirname(__file__), "workspace")
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.mkdir(workspace_dir)
    os.environ["WORKSPACE"] = workspace_dir
    os.chdir(workspace_dir)


class TestFileServer(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_file_server(self):
        name = "FAKE_NEXUS"
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)

        context.kill(name)
        self.assertEqual(context.get_service(name).status(), [])
        time.sleep(2)

        response1 = actions.start_one(context, name, True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service(name).status())
        response2 = actions.start_one(context, name, True, False, None, port=None)
        self.assertFalse(response2)
        context.kill(name)
        self.assertEqual(context.get_service(name).status(), [])


class TestNexus(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_nexus_zip(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")

        # start fake nexus
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        context = SmContext(SmApplication(config_dir_override), None, False, False)
        servicetostart = "PLAY_NEXUS_END_TO_END_TEST"
        actions.start_one(context, servicetostart, True, False, None, port=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart)

        context.kill("FAKE_NEXUS")

        self.assertEqual(context.get_service(servicetostart).status(), [])
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])

    def test_nexus_tgz(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")

        # start fake nexus
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        context = SmContext(SmApplication(config_dir_override), None, False, False)
        servicetostart = "PLAY_NEXUS_TGZ_TEST"
        actions.start_one(context, servicetostart, True, False, None, port=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart)

        context.kill("FAKE_NEXUS")

        self.assertEqual(context.get_service(servicetostart).status(), [])
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])


class TestBintray(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_bintray(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")

        # start fake bintray
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        response1 = actions.start_one(context, "FAKE_BINTRAY", True, False, None, port=None)
        self.assertIsNotNone(context.get_service("FAKE_BINTRAY").status())
        time.sleep(5)

        context = SmContext(SmApplication(config_dir_override), None, False, False)
        servicetostart = "PLAY_BINTRAY_END_TO_END_TEST"
        actions.start_one(context, servicetostart, True, False, None, port=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart)

        context.kill("FAKE_BINTRAY")

        self.assertEqual(context.get_service(servicetostart).status(), [])
        self.assertEqual(context.get_service("FAKE_BINTRAY").status(), [])


class TestActions(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_start_and_stop_one(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        actions.start_one(context, "TEST_ONE", True, False, None, port=None)
        self.assertEquals(len(context.get_service("TEST_ONE").status()), 1)
        context.kill("TEST_ONE")
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_start_and_stop_one_with_append_args(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        actions.start_one(context, "TEST_ONE", True, False, None, None, ["; echo 'Fin du sleep!!'"])
        self.assertEquals(len(context.get_service("TEST_ONE").status()), 2) # it is two in this case because the append creates a forked process
        context.kill("TEST_ONE")
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_dropwizard_from_source(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        servicetostart = "DROPWIZARD_NEXUS_END_TO_END_TEST"
        actions.start_and_wait(service_resolver, context, [servicetostart], False, False, None, port=None, seconds_to_wait=90, append_args=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart)
        self.assertEqual(context.get_service(servicetostart).status(), [])

    def test_dropwizard_from_jar(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        # start fake nexus
        actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        servicetostart = "DROPWIZARD_NEXUS_END_TO_END_TEST"
        actions.start_and_wait(service_resolver, context, [servicetostart], True, False, None, port=None, seconds_to_wait=90, append_args=None)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart)
        context.kill("FAKE_NEXUS")
        time.sleep(5)
        self.assertEqual(context.get_service(servicetostart).status(), [])
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])

    def test_play_from_source(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        servicetostart = "PLAY_NEXUS_END_TO_END_TEST"
        port = None
        secondsToWait = 90
        append_args = None
        actions.start_and_wait(service_resolver, context, [servicetostart], False, False, None, port, secondsToWait, append_args)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart)
        self.assertEqual(context.get_service(servicetostart).status(), [])

    def test_successful_play_from_jar_without_waiting(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        context.kill_everything()
        time.sleep(5)

        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

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
            context.kill_everything()

    def test_successful_play_from_jar_without_waiting_with_append_args(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        context.kill_everything()
        time.sleep(5)

        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, None, None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        servicetostart = ["PLAY_NEXUS_END_TO_END_TEST"]
        appendArgs = {"PLAY_NEXUS_END_TO_END_TEST": ["-DFoo=Bar"]}
        fatJar = True
        release = False
        proxy = None
        port = None
        seconds_to_wait = None

        try:
            actions.start_and_wait(service_resolver, context, servicetostart, fatJar, release, proxy, port, seconds_to_wait, appendArgs)
            time.sleep(5)
            service = SmPlayService(context, "PLAY_NEXUS_END_TO_END_TEST")
            processes = SmProcess.processes_matching(service.pattern)
            self.assertEqual(len(processes), 1)
            self.assertTrue("-DFoo=Bar" in processes[0].args)
        finally:
            context.kill_everything()

    def test_failing_play_from_jar(self):

        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)

        context.kill_everything()
        time.sleep(5)

        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        try:
            servicetostart = ["BROKEN_PLAY_PROJECT"]
            actions.start_and_wait(service_resolver, context, servicetostart, fatjar=True, release=False, proxy=None, port=None, seconds_to_wait=2, append_args=None)
            self.fail("Did not expect the project to startup.")
        except ServiceManagerException as sme:
            self.assertEqual("Timed out starting service(s): BROKEN_PLAY_PROJECT", sme.message)
        finally:
            context.kill_everything()


    def test_start_and_stop_one_duplicate(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        response1 = actions.start_one(context, "TEST_ONE", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        response2 = actions.start_one(context, "TEST_ONE", True, False, None, port=None)
        self.assertFalse(response2)
        context.kill("TEST_ONE")
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_assets_server(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()

        context.kill("FAKE_NEXUS")
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])
        time.sleep(2)

        # start fake nexus
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])
        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        actions.start_one(context, "PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", True, False, None, port=None)
        self.assertIsNotNone(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status())
        context.kill("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND")
        context.kill("FAKE_NEXUS")
        time.sleep(15)

        self.assertEqual(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status(), [])
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])

    def test_wait_on_assets_server(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        sm_application = SmApplication(config_dir_override)
        context = SmContext(sm_application, None, False, False)
        service_resolver = ServiceResolver(sm_application)
        context.kill_everything()

        context.kill("FAKE_NEXUS")
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])
        time.sleep(2)

        # start fake nexus
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])
        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        port = None
        seconds_to_wait = 5
        append_args = None
        actions.start_and_wait(service_resolver, context, ["PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND"], True, False, None, port, seconds_to_wait, append_args)
        self.assertIsNotNone(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status())
        context.kill("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND")
        context.kill("FAKE_NEXUS")
        time.sleep(15)

        self.assertEqual(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status(), [])
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])

    def test_python_server_offline(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, True, False)
        port = None
        append_args = None
        actions.start_one(context, "PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", True, False, None, port, append_args)
        self.assertIsNotNone(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status())
        context.kill("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND")
        time.sleep(5)
        self.assertEqual(context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND").status(), [])

class TestStartCommands(unittest.TestCase):

    def setUp(self):
        set_up_and_clean_workspace()

    def test_play_binary_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("PLAY_NEXUS_END_TO_END_TEST", True, False, None, port=None)
        #starter = SmPlayServiceStarter(context, "PLAY_NEXUS_END_TO_END_TEST", True, False, None, None, None, None)
        expected = [ './basicplayapp/bin/basicplayapp',
                                '-DProd.microservice.whitelist.useWhitelist=false',
                                '-DProd.mongodb.uri=mongodb://localhost:27017/auth',
                                '-J-Xmx256m',
                                '-J-Xms256m',
                                '-J-XX:MaxPermSize=128m',
                                '-Dhttp.port=8500',
                                '-Dservice.manager.serviceName=PLAY_NEXUS_END_TO_END_TEST',
                                '-Dservice.manager.runFrom=True']
        self.assertEqual(starter.get_start_command("BINARY"), expected)

    def test_play_source_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("PLAY_NEXUS_END_TO_END_TEST", True, False, None, port=None)
        expected = [ 'play', 'start -Dhttp.port=8500 -Dservice.manager.serviceName=PLAY_NEXUS_END_TO_END_TEST -Dservice.manager.runFrom=True -DFoo=false']
        self.assertEqual(starter.get_start_command("SOURCE"), expected)

    def test_dropwizard_binary_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("DROPWIZARD_NEXUS_END_TO_END_TEST", "foo", proxy=None)
        expected = [
            'java',
            '-Dfile.encoding=UTF8',
            '-Xmx64M',
            '-XX:+CMSClassUnloadingEnabled',
            '-XX:MaxPermSize=64m',
            '-Ddw.http.port=8080',
            '-Dservice.manager.serviceName=DROPWIZARD_NEXUS_END_TO_END_TEST',
            '-Dservice.manager.serviceName=DROPWIZARD_NEXUS_END_TO_END_TEST',
            '-Dservice.manager.runFrom=foo',
            '-jar',
            'dwtest-foo-shaded.jar',
            'server',
            'dev_config.yml']
        cmd = starter.get_start_command("BINARY")
        cmd[-1] = cmd[-1].split("/")[-1]
        cmd[0] = cmd[0].split("/")[-1]
        cmd[len(cmd) -3] = cmd[len(cmd) -3].split("/")[-1]
        self.assertEqual(cmd, expected)

    def test_dropwizard_source_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("DROPWIZARD_NEXUS_END_TO_END_TEST", "foo", proxy=None)
        expected = ['./startappfromcode.sh']
        self.assertEqual(starter.get_start_command("SOURCE"), expected)

    def test_python_binary_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", "foo", proxy=None)
        expected = ['python -m SimpleHTTPServer 9032']
        cmd = starter.get_start_command("BINARY")
        self.assertEqual(cmd, expected)

    def test_python_source_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", "foo", proxy=None)
        expected = ['python -m SimpleHTTPServer 9032']
        self.assertEqual(starter.get_start_command("SOURCE"), expected)

    def test_external_binary_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("FAKE_NEXUS", "foo", proxy=None)
        expected = [ 'python', 'fakenexus.py']
        cmd = starter.get_start_command("BINARY") #context will be ignored
        self.assertEqual(cmd, expected)

    def test_external_source_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        starter = context.get_service_starter("FAKE_NEXUS", "foo", proxy=None)
        expected = [ 'python', 'fakenexus.py']
        self.assertEqual(starter.get_start_command("SOURCE"), expected) #context will be ignored

class TestServerFunctionality(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_simple(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()
        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                               {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                               {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything()
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_play_with_append_args(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()

        # Start up fake nexus first
        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT", "appendArgs": ["-Dfoo=bar"]}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()
        time.sleep(5)
        self.assertEqual(len(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status()), 1)
        service = SmPlayService(context, "PLAY_NEXUS_END_TO_END_TEST")
        processes = SmProcess.processes_matching(service.pattern)
        self.assertEqual(len(processes), 1)
        self.assertTrue("-Dfoo=bar" in processes[0].args)
        context.kill_everything()
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_play_with_invalid_append_args(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()
        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT", "appendArgs": "-Dfoo=bar"}]
        with pytest.raises(BadRequestException):
            smserverlogic.SmStartRequest(server, request, True, False).process_request()

    def test_external_with_append_args(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()
        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT", "appendArgs": [";echo foo"]}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        pattern = context.application.services["TEST_ONE"]["pattern"]
        processes = SmProcess.processes_matching(pattern)
        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        self.assertEqual(len(processes), 2) #we expect two proecesses to be spawned because of the appended command
        self.assertTrue(";echo" in processes[0].args or ";echo" in processes[1].args)
        context.kill_everything()
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_external_with_invalid_append_args(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()
        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT", "appendArgs": ";echo foo"}]
        with pytest.raises(BadRequestException):
            smserverlogic.SmStartRequest(server, request, True, False).process_request()

    def test_offline(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()
        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))
        request = dict()
        request["testId"] = "foo"
        request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                               {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                               {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]
        smserverlogic.SmStartRequest(server, request, True, False).process_request()
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything()
        self.assertEqual(context.get_service("TEST_ONE").status(), [])
        request["testId"] = "foo2"
        smserverlogic.SmStartRequest(server, request, True, True).process_request()
        self.assertIsNotNone(context.get_service("TEST_ONE").status())
        # stop does not currently work for extern
        #smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything()
        self.assertEqual(context.get_service("TEST_ONE").status(), [])

    def test_ensure_multiple_instances_of_a_service_can_be_started_from_server(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.kill_everything()
        server = smserverlogic.SmServer(SmApplication(config_dir_override, None))

        # start fake nexus
        self.assertEqual(context.get_service("FAKE_NEXUS").status(), [])
        response1 = actions.start_one(context, "FAKE_NEXUS", True, False, None, port=None)
        self.assertTrue(response1)
        self.assertIsNotNone(context.get_service("FAKE_NEXUS").status())
        time.sleep(5)

        first_request = dict()
        first_request["testId"] = "multiple-instance-unit-test-1"
        first_request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                                     {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                                     {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]
        request = smserverlogic.SmStartRequest(server, first_request, True, False)
        request.process_request()

        time.sleep(5)
        self.assertEqual(len(context.get_service("TEST_ONE").status()), 1)
        self.assertEqual(len(context.get_service("DROPWIZARD_NEXUS_END_TO_END_TEST").status()), 1)
        self.assertEqual(len(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status()), 1)

        second_request = dict()
        second_request["testId"] = "multiple-instance-unit-test-2"
        second_request["services"] = [{"serviceName": "TEST_ONE", "runFrom": "SNAPSHOT"},
                                      {"serviceName": "DROPWIZARD_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"},
                                      {"serviceName": "PLAY_NEXUS_END_TO_END_TEST", "runFrom": "SNAPSHOT"}]
        smserverlogic.SmStartRequest(server, second_request, True, False).process_request()
        time.sleep(5)
        self.assertEqual(len(context.get_service("TEST_ONE").status()), 2)
        self.assertEqual(len(context.get_service("DROPWIZARD_NEXUS_END_TO_END_TEST").status()), 2)
        self.assertEqual(len(context.get_service("PLAY_NEXUS_END_TO_END_TEST").status()), 2)

        # stop does not currently work for extern
        # smserverlogic.SmStopRequest(SERVER, request).process_request()
        context.kill_everything()
        self.assertEqual(context.get_service("TEST_ONE").status(), [])
        context.kill("FAKE_NEXUS")


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        application = SmApplication(config_dir_override, None)
        self.assertEqual(len(application.services), 13)
        self.assertEqual(application.services["TEST_TEMPLATE"]["type"], "external")
        self.assertEqual(application.services["TEST_TEMPLATE"]["pattern"], "some.namespace=TEST_TEMPLATE")
        self.assertEqual(application.services["TEST_TEMPLATE"]["includeInStartAndStopAll"], False)
        self.assertEqual(application.services["TEST_TEMPLATE"]["some_parameter"], "value we expect")
        self.assertEqual(application.services["TEST_TEMPLATE"]["anestedvalue"]["anotherunique"], "value")
        self.assertEqual(application.services["TEST_TEMPLATE"]["anestedvalue"]["new"], "and this value")
        self.assertEqual(application.services["TEST_TEMPLATE"]["anestedvalue"]["override"], "will have this value")
        self.assertEqual(len(application.services["TEST_TEMPLATE"]), 8)


class TestServiceResolver(unittest.TestCase):
    def setUp(self):
        set_up_and_clean_workspace()

    def test_config(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        application = SmApplication(config_dir_override, None)
        service_resolver = ServiceResolver(application)
        nexus_wildcard = service_resolver.resolve_services("PLAY_NEXU*TEST")
        self.assertTrue("PLAY_NEXUS_END_TO_END_TEST" in nexus_wildcard)
        self.assertEqual(3, len(nexus_wildcard))

        all_services = service_resolver.resolve_services("*")
        self.assertTrue("TEST_ONE" in all_services)
        self.assertTrue("TEST_TWO" in all_services)
        self.assertTrue("TEST_THREE" in all_services)
        self.assertTrue("TEST_TEMPLATE" in all_services)
        self.assertTrue("DROPWIZARD_NEXUS_END_TO_END_TEST" in all_services)
        self.assertTrue("PLAY_NEXUS_END_TO_END_TEST" in all_services)
        self.assertTrue("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND" in all_services)
        self.assertEqual(13, len(all_services))

        test_profile = service_resolver.resolve_services("TEST")
        self.assertTrue("TEST_ONE" in test_profile)
        self.assertTrue("TEST_TWO" in test_profile)
        self.assertTrue("TEST_THREE" in test_profile)
        self.assertTrue("TEST_TEMPLATE" in test_profile)
        self.assertEqual(4, len(test_profile))

        tests_without_one = service_resolver.resolve_services_from_array(["TEST", "-TEST_ONE"])
        self.assertFalse("TEST_ONE" in tests_without_one)
        self.assertTrue("TEST_TWO" in tests_without_one)
        self.assertTrue("TEST_THREE" in tests_without_one)
        self.assertTrue("TEST_TEMPLATE" in tests_without_one)
        self.assertEqual(3, len(tests_without_one))

        tests_without_one = service_resolver.resolve_services_from_array(["TEST_WILD_CARD_NEGATED_PROFILE"])
        self.assertTrue("TEST_ONE" in tests_without_one)
        self.assertFalse("TEST_TWO" in tests_without_one)
        self.assertTrue("TEST_THREE" in tests_without_one)
        self.assertTrue("TEST_TEMPLATE" in tests_without_one)
        self.assertEqual(3, len(tests_without_one))

        nothing = service_resolver.resolve_services_from_array(["*", "-*"])
        self.assertEqual(0, len(nothing))

        test_template = service_resolver.resolve_services("TEST_WILD_CARD_PROFILE")
        self.assertTrue("TEST_TEMPLATE" in test_template)
        self.assertEqual(1, len(test_template))


class TestConfig(unittest.TestCase):
    def test_runfrom_override(self):
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        python_server = context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND")
        run_from = context.get_run_from_service_override_value_or_use_default(python_server, "SHOULD_BE_OVERWRITTEN")
        self.assertEqual(run_from, "RELEASE")


class TestCredentialsResolver(unittest.TestCase):

    defaultEnv = os.environ.copy()

    def test_env_nexus_creds(self):
        os.environ.clear()
        os.environ.update(self.defaultEnv)
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        creds = EnvNexusCredentials(context)
        resolver = CredentialsResolver(context)

        os.environ["NEXUS_PASS"] = "lame"
        os.environ["NEXUS_USER"] = "lame_user"

        self.assertEqual(creds.load_creds(), ("lame_user", "lame"))
        self.assertEqual(resolver.resolve_nexus_credentials(), {"user": "lame_user", "password": "lame"})


    def test_env_nexus_creds_from_config(self):
        os.environ.clear()
        os.environ.update(self.defaultEnv)
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.application.config["nexusPasswordEnvironmentVar"] = "A_FREAKIN_PASS_ENV_VAR"
        context.application.config["nexusUserEnvironmentVar"] = "A_FREAKIN_USER_ENV_VAR"
        creds = EnvNexusCredentials(context)
        resolver = CredentialsResolver(context)

        os.environ.setdefault("A_FREAKIN_PASS_ENV_VAR", "lame_from_conf")
        os.environ.setdefault("A_FREAKIN_USER_ENV_VAR", "lame_user_from_conf")

        self.assertEqual(creds.load_creds(), ("lame_user_from_conf", "lame_from_conf"))
        self.assertEqual(resolver.resolve_nexus_credentials(), {"user": "lame_user_from_conf", "password": "lame_from_conf"})

    def test_sbt_nexus_creds_from_config(self):
        os.environ.clear()
        os.environ.update(self.defaultEnv)
        config_dir_override = os.path.join(os.path.dirname(__file__), "conf")
        context = SmContext(SmApplication(config_dir_override), None, False, False)
        context.application.config["sbtCredentialsFile"] = os.path.dirname(__file__) + "/.sbt/.credentials"

        creds = SbtNexusCredentials(context)
        resolver = CredentialsResolver(context)

        self.assertEqual(creds.load_creds(), ("sbt", "sbt_creds"))
        self.assertEqual(resolver.resolve_nexus_credentials(), {"user": "sbt", "password": "sbt_creds"})


if __name__ == '__main__':
    unittest.main()
