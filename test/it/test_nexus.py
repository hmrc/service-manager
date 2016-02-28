from testbase import TestBase

class TestNexus(TestBase):

    def test_nexus_zip(self):
        self.startFakeNexus()
        context = self.createContext()
        servicetostart = "PLAY_NEXUS_END_TO_END_TEST"
        self.start_service_and_wait(context, servicetostart)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)

        self.assertEqual(context.get_service(servicetostart).status(), [])

    def test_nexus_tgz(self):
        self.startFakeNexus()
        context = self.createContext()
        servicetostart = "PLAY_NEXUS_TGZ_TEST"
        self.start_service_and_wait(context, servicetostart)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)

        self.assertEqual(context.get_service(servicetostart).status(), [])

