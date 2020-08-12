from .testbase import TestBase


class TestArtifactory(TestBase):
    def test_artifactory(self):

        self.startFakeArtifactory()

        context = self.createContext()
        servicetostart = "PLAY_ARTIFACTORY_END_TO_END_TEST"
        self.start_service_and_wait(context, servicetostart)
        self.assertIsNotNone(context.get_service(servicetostart).status())
        context.kill(servicetostart, True)

        self.assertEqual(context.get_service(servicetostart).status(), [])
