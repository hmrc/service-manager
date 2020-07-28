import os

from abc import abstractmethod


class CredentialsResolver:
    def __init__(self, context):
        self.context = context
        self.credential_resolvers = [
            EnvNexusCredentials(context),
            SbtNexusCredentials(context),
        ]
        self.credentials = None

    def resolve_nexus_credentials(self):
        if not self.credentials:
            self.credentials = self._resolve_credentials()
        return self.credentials

    def _resolve_credentials(self):
        for creds in self.credential_resolvers:
            if creds.exist():
                self.context.log("Resolved nexus credentials from: %s" % creds.describe(), True)
                (user, password) = creds.load_creds()
                self.credentials = {"user": user, "password": password}
                return self.credentials
        self.context.log("Could not resolve nexus credentials!!! Downloading artifacts will fail")
        return None


class NexusCredentials:
    def __init__(self, context):
        self.context = context
        pass

    @abstractmethod
    def load_creds(self):
        pass

    @abstractmethod
    def exist(self):
        pass

    @abstractmethod
    def describe(self):
        pass


class SbtNexusCredentials(NexusCredentials):
    def __init__(self, context):
        NexusCredentials.__init__(self, context)
        self.sbt_location = context.config_value("sbtCredentialsFile", os.environ["HOME"] + "/.sbt/.credentials")

    def load_creds(self):
        creds = {
            key.strip(): value.strip()
            for (key, value) in [x.split("=") for x in open(self.sbt_location, "r").readlines()]
        }
        return creds["user"], creds["password"]

    def exist(self):
        found = os.path.exists(self.sbt_location)
        if found:
            user, password = self.load_creds()
            found = user and password
        return found

    def describe(self):
        return "sbt credentials file (%s)" % self.sbt_location


class EnvNexusCredentials(NexusCredentials):
    def __init__(self, context):
        NexusCredentials.__init__(self, context)
        self.nexus_pass_env_var = context.config_value("nexusPasswordEnvironmentVar", "NEXUS_PASS")
        self.nexus_user_env_var = context.config_value("nexusUserEnvironmentVar", "NEXUS_USER")

    def load_creds(self):
        return (
            os.environ.get(self.nexus_user_env_var, None),
            os.environ.get(self.nexus_pass_env_var, None),
        )

    def exist(self):
        (nexus_user, nexus_password) = self.load_creds()
        found = nexus_user and nexus_password
        return found

    def describe(self):
        return "environment variables (%s and %s)" % (self.nexus_user_env_var, self.nexus_pass_env_var,)
