from servicemanager.smcontext import SmApplication, SmContext

from testbase import TestBase

class TestConfiguration(TestBase):

    def test_config(self):
        application = SmApplication(self.config_dir_override, None)
        self.assertEqual(len(application.services), 13)
        self.assertEqual(application.services["TEST_TEMPLATE"]["type"], "external")
        self.assertEqual(application.services["TEST_TEMPLATE"]["pattern"], "some.namespace=TEST_TEMPLATE")
        self.assertEqual(application.services["TEST_TEMPLATE"]["includeInStartAndStopAll"], False)
        self.assertEqual(application.services["TEST_TEMPLATE"]["some_parameter"], "value we expect")
        self.assertEqual(application.services["TEST_TEMPLATE"]["anestedvalue"]["anotherunique"], "value")
        self.assertEqual(application.services["TEST_TEMPLATE"]["anestedvalue"]["new"], "and this value")
        self.assertEqual(application.services["TEST_TEMPLATE"]["anestedvalue"]["override"], "will have this value")
        self.assertEqual(len(application.services["TEST_TEMPLATE"]), 8)

    def test_runfrom_override(self):
        context = SmContext(SmApplication(self.config_dir_override), None, False, False)
        python_server = context.get_service("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND")
        run_from = context.get_run_from_service_override_value_or_use_default(python_server, "SHOULD_BE_OVERWRITTEN")
        self.assertEqual(run_from, "RELEASE")
