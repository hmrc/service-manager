import os
import sys

# dont do this in production code, this is bad practice it would seem, only for tests
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../../servicemanager'))

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

from servicemanager.smcredentials import EnvNexusCredentials, CredentialsResolver, SbtNexusCredentials

import unittest

class TestBase(unittest.TestCase):

    config_dir_override = os.path.join(os.path.dirname(__file__), "../conf")

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

    def startService(self, context, servicetostart): actions.start_one(context, servicetostart, True, False, None, port=None)

    def startFakeBintray(self):
        self.bintrayContext = self.createContext()
        self.startService(self.bintrayContext, "FAKE_BINTRAY")
        self.assertIsNotNone(self.bintrayContext.get_service("FAKE_BINTRAY").status())

    def startFakeNexus(self):
        self.nexusContext = self.createContext()
        self.startService(self.nexusContext, "FAKE_NEXUS")
        self.assertIsNotNone(self.nexusContext.get_service("FAKE_NEXUS").status())

    def stopFakeNexus(self):
        if self.nexusContext is not None:
            self.nexusContext.kill("FAKE_NEXUS", True)
            self.assertEqual(self.nexusContext.get_service("FAKE_NEXUS").status(), [])

    def stopFakeBintray(self):
        if self.bintrayContext is not None:
            self.bintrayContext.kill("FAKE_BINTRAY", True)
            self.assertEqual(self.bintrayContext.get_service("FAKE_BINTRAY").status(), [])