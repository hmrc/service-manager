from servicemanager.smcredentials import EnvNexusCredentials, CredentialsResolver, SbtNexusCredentials
import os

from testbase import TestBase

class TestCredentialsResolver(TestBase):

    defaultEnv = os.environ.copy()

    def test_env_nexus_creds(self):
        os.environ.clear()
        os.environ.update(self.defaultEnv)
        context = self.createContext()
        creds = EnvNexusCredentials(context)
        resolver = CredentialsResolver(context)

        os.environ["NEXUS_PASS"] = "lame"
        os.environ["NEXUS_USER"] = "lame_user"

        self.assertEqual(creds.load_creds(), ("lame_user", "lame"))
        self.assertEqual(resolver.resolve_nexus_credentials(), {"user": "lame_user", "password": "lame"})


    def test_env_nexus_creds_from_config(self):
        os.environ.clear()
        os.environ.update(self.defaultEnv)

        context = self.createContext()
        context.application.config["nexusPasswordEnvironmentVar"] = "A_FREAKIN_PASS_ENV_VAR"
        context.application.config["nexusUserEnvironmentVar"] = "A_FREAKIN_USER_ENV_VAR"
        creds = EnvNexusCredentials(context)
        resolver = CredentialsResolver(context)

        os.environ.setdefault("A_FREAKIN_PASS_ENV_VAR", "lame_from_conf")
        os.environ.setdefault("A_FREAKIN_USER_ENV_VAR", "lame_user_from_conf")

        self.assertEqual(creds.load_creds(), ("lame_user_from_conf", "lame_from_conf"))
        self.assertEqual(resolver.resolve_nexus_credentials(), {"user": "lame_user_from_conf", "password": "lame_from_conf"})

    def test_sbt_nexus_creds_from_config(self):
        os.environ.clear()
        os.environ.update(self.defaultEnv)
        context = self.createContext()
        context.application.config["sbtCredentialsFile"] = os.path.dirname(__file__) + "/../.sbt/.credentials"

        creds = SbtNexusCredentials(context)
        resolver = CredentialsResolver(context)

        self.assertEqual(creds.load_creds(), ("sbt", "sbt_creds"))
        self.assertEqual(resolver.resolve_nexus_credentials(), {"user": "sbt", "password": "sbt_creds"})