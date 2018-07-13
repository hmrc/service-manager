import os
import sys
from smnexus import SmNexus
from smbintray import SmBintray
from smartifactory import SmArtifactory


class SmArtifactRepoFactory():

    @staticmethod
    def get_repository(context, service_name, service_binary_config):
      repo = service_binary_config["repo"]
      if repo == "nexus":
        return SmNexus(context, service_name)
      elif repo == "bintray":
        return SmBintray(context, service_name)
      elif repo == "artifactory":
        return SmArtifactory(context, service_name)
      else:
        raise Exception("Unrecognised binary repo configuration: %s. Supported values are 'nexus', 'bintray' and 'artifactory'" % repo)


    @staticmethod
    def get_play_app_extension(service_binary_config):
        ext = service_binary_config.get("ext", "tgz")
        return "." + ext


