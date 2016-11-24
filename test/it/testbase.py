import os
import sys

# dont do this in production code, this is bad practice it would seem, only for tests
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../../servicemanager'))

from servicemanager.actions import actions
from servicemanager.serviceresolver import ServiceResolver
from servicemanager.smcontext import SmApplication, SmContext

import time
import shutil
import unittest
from servicemanager import subprocess

class TestBase(unittest.TestCase):

    config_dir_override = os.path.join(os.path.dirname(__file__), "../conf")
    default_time_out = 10

    def setUp(self):
        self.set_up_and_clean_workspace()
        self.bintrayContext = None
        self.nexusContext = None

    def tearDown(self):
        self.stopFakeBintray()
        self.stopFakeNexus()


    def set_up_and_clean_workspace(self):
        workspace_dir = os.path.join(os.path.dirname(__file__), "workspace")
        if os.path.exists(workspace_dir):
            shutil.rmtree(workspace_dir)
        os.mkdir(workspace_dir)
        os.environ["WORKSPACE"] = workspace_dir
        os.chdir(workspace_dir)

    def createContext(self): return SmContext(SmApplication(self.config_dir_override), None, False, False)

    def start_service_and_wait(self, context, servicetostart):
        sm_application = SmApplication(self.config_dir_override)
        service_resolver = ServiceResolver(sm_application)
        actions.start_and_wait(service_resolver, context, [servicetostart], fatjar=True, release=False, proxy=None, port=None, seconds_to_wait=5, append_args=None)

    def startFakeBintray(self):
        self.bintrayContext = self.createContext()
        self.start_service_and_wait(self.bintrayContext, "FAKE_BINTRAY")
        self.assertIsNotNone(self.bintrayContext.get_service("FAKE_BINTRAY").status())

    def startFakeNexus(self):
        self.nexusContext = self.createContext()
        self.start_service_and_wait(self.nexusContext, "FAKE_NEXUS")
        self.assertIsNotNone(self.nexusContext.get_service("FAKE_NEXUS").status())

    def stopFakeNexus(self):
        if self.nexusContext is not None:
            self.nexusContext.kill("FAKE_NEXUS", True)
            self.assertEqual(self.nexusContext.get_service("FAKE_NEXUS").status(), [])

    def stopFakeBintray(self):
        if self.bintrayContext is not None:
            self.bintrayContext.kill("FAKE_BINTRAY", True)
            self.assertEqual(self.bintrayContext.get_service("FAKE_BINTRAY").status(), [])

    def waitForCondition(self, f, expected, time_out_secs = default_time_out):
        dead_line = time.time() + time_out_secs
        value = None
        while (time.time() < dead_line):
            value = f()
            if value == expected: return
            time.sleep(0.1)

        command = "ps -eo ppid,pid,etime,rss,args"
        ps_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        stdout, stderr = ps_command.communicate()
        print(stdout)
        
        self.assertEquals(value, expected)