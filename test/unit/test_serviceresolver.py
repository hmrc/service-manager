from servicemanager.smcontext import SmApplication
from servicemanager.serviceresolver import ServiceResolver

from testbase import TestBase

class TestServiceResolver(TestBase):

    def test_config(self):
        application = SmApplication(self.config_dir_override, None)
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