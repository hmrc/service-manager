import unittest
import os
from hamcrest import *

from service.smplayservice import SmPlayServiceStarter
from smcontext import SmContext, SmApplication

class TestSmPlayService(unittest.TestCase):
  test_dir = os.path.join(os.path.dirname(__file__), "../")

  def setUp(self):
    sm_application = SmApplication(self.test_dir + "conf/", features = {})
    sm_context = SmContext(sm_application, "")
    self.sm_play_service = SmPlayServiceStarter(sm_context, "PLAY_NEXUS_END_TO_END_TEST", "", "", 9000, "", "", "", "")

  def test_closed_assets_config(self):
    assert_that(self.sm_play_service._get_assets_version(self.test_dir + "testapps/basicplayapp"), contains_inanyorder("2.149.0", "2.150.0"))

  def test_open_assets_config(self):
    assert_that(self.sm_play_service._get_assets_version(self.test_dir + "testapps/openplayapp"), has_item("2.150.0"))
