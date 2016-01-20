import unittest
from hamcrest import *

from service.smplayservice import SmPlayServiceStarter
from smcontext import SmContext, SmApplication

class TestSmPlayService(unittest.TestCase):
  def setUp(self):
    sm_application = SmApplication("test/conf/", features = {})
    sm_context = SmContext(sm_application, "")
    self.sm_play_service = SmPlayServiceStarter(sm_context, "PLAY_NEXUS_END_TO_END_TEST", "", "", 9000, "", "", "", "")

  def test_closed_assets_config(self):
    assert_that(self.sm_play_service._get_assets_version("test/testapps/basicplayapp"), has_item("2.149.0"))

  def test_open_assets_config(self):
    assert_that(self.sm_play_service._get_assets_version("test/testapps/openplayapp"), has_item("2.150.0"))
