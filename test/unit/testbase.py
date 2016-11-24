import os
import sys

# dont do this in production code, this is bad practice it would seem, only for tests
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../../servicemanager'))

from servicemanager.smcontext import SmApplication, SmContext

import unittest

class TestBase(unittest.TestCase):

    config_dir_override = os.path.join(os.path.dirname(__file__), "../conf")

    def createContext(self): return SmContext(SmApplication(self.config_dir_override), None, False, False)
