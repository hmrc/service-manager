import unittest
import os

from servicemanager.actions.actions import get_start_cmd
from servicemanager.smcontext import SmApplication, SmContext, ServiceManagerException

class TestGetStartCmd(unittest.TestCase):

    def test_returns_start_command_based_on_configuration_file(self):
        test_id = "get_start_command_test_id"
        config_dir_override = os.path.join(os.path.dirname(__file__), "../conf")
        context = SmContext(SmApplication(config_dir_override), test_id, None, None)

        start_cmd = get_start_cmd(context, service_name = "TEST_ONE", fatjar = False, release = "LATEST", proxy = "", port=None, appendArgs=None)
        self.assertEqual(start_cmd, ["sleep", "99087347347346734673872"])

