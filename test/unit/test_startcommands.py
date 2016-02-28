from testbase import TestBase

class TestStartCommands(TestBase):

    def test_play_binary_config(self):
        context = self.createContext()
        starter = context.get_service_starter("PLAY_NEXUS_END_TO_END_TEST", True, False, None, port=None)
        #starter = SmPlayServiceStarter(context, "PLAY_NEXUS_END_TO_END_TEST", True, False, None, None, None, None)
        expected = [ './basicplayapp/bin/basicplayapp',
                     '-DProd.microservice.whitelist.useWhitelist=false',
                     '-DProd.mongodb.uri=mongodb://localhost:27017/auth',
                     '-J-Xmx256m',
                     '-J-Xms256m',
                     '-J-XX:MaxPermSize=128m',
                     '-Dhttp.port=8500',
                     '-Dservice.manager.serviceName=PLAY_NEXUS_END_TO_END_TEST',
                     '-Dservice.manager.runFrom=True']
        self.assertEqual(starter.get_start_command("BINARY"), expected)

    def test_play_source_config(self):
        context = self.createContext()
        starter = context.get_service_starter("PLAY_NEXUS_END_TO_END_TEST", True, False, None, port=None)
        expected = [ 'play', 'start -Dhttp.port=8500 -Dservice.manager.serviceName=PLAY_NEXUS_END_TO_END_TEST -Dservice.manager.runFrom=True -DFoo=false']
        self.assertEqual(starter.get_start_command("SOURCE"), expected)

    def test_dropwizard_binary_config(self):
        context = self.createContext()
        starter = context.get_service_starter("DROPWIZARD_NEXUS_END_TO_END_TEST", "foo", proxy=None)
        expected = [
            'java',
            '-Dfile.encoding=UTF8',
            '-Xmx64M',
            '-XX:+CMSClassUnloadingEnabled',
            '-XX:MaxPermSize=64m',
            '-Ddw.http.port=8080',
            '-Dservice.manager.serviceName=DROPWIZARD_NEXUS_END_TO_END_TEST',
            '-Dservice.manager.serviceName=DROPWIZARD_NEXUS_END_TO_END_TEST',
            '-Dservice.manager.runFrom=foo',
            '-jar',
            'dwtest-foo-shaded.jar',
            'server',
            'dev_config.yml']
        cmd = starter.get_start_command("BINARY")
        cmd[-1] = cmd[-1].split("/")[-1]
        cmd[0] = cmd[0].split("/")[-1]
        cmd[len(cmd) -3] = cmd[len(cmd) -3].split("/")[-1]
        self.assertEqual(cmd, expected)

    def test_dropwizard_source_config(self):
        context = self.createContext()
        starter = context.get_service_starter("DROPWIZARD_NEXUS_END_TO_END_TEST", "foo", proxy=None)
        expected = ['./startappfromcode.sh']
        self.assertEqual(starter.get_start_command("SOURCE"), expected)

    def test_python_binary_config(self):
        context = self.createContext()
        starter = context.get_service_starter("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", "foo", proxy=None)
        expected = ['python -m SimpleHTTPServer 9032']
        cmd = starter.get_start_command("BINARY")
        self.assertEqual(cmd, expected)

    def test_python_source_config(self):
        context = self.createContext()
        starter = context.get_service_starter("PYTHON_SIMPLE_SERVER_ASSETS_FRONTEND", "foo", proxy=None)
        expected = ['python -m SimpleHTTPServer 9032']
        self.assertEqual(starter.get_start_command("SOURCE"), expected)

    def test_external_binary_config(self):
        context = self.createContext()
        starter = context.get_service_starter("FAKE_NEXUS", "foo", proxy=None)
        expected = [ 'python', 'fakenexus.py']
        cmd = starter.get_start_command("BINARY") #context will be ignored
        self.assertEqual(cmd, expected)

    def test_external_source_config(self):
        context = self.createContext()
        starter = context.get_service_starter("FAKE_NEXUS", "foo", proxy=None)
        expected = [ 'python', 'fakenexus.py']
        self.assertEqual(starter.get_start_command("SOURCE"), expected) #context will be ignored