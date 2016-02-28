from testbase import TestBase

class TestBintray(TestBase):
    def test_bintray(self):

        self.startFakeBintray()

        context = self.createContext()
        servicetostart = "PLAY_BINTRAY_END_TO_END_TEST"
        self.start_service_and_wait(context, servicetostart)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)

        self.assertEqual(context.get_service(servicetostart).status(), [])
