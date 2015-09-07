import os
import sys
from smnexus import SmNexus
from smbintray import SmBintray


class SmArtifactRepoFactory():

    @staticmethod
    def get_repository(context, service_name, service_binary_config):
    	if SmArtifactRepoFactory._is_nexus(service_binary_config):
            return SmNexus(context, service_name)
        else:
            return SmBintray(context, service_name)

    @staticmethod
    def get_play_app_extension(service_binary_config):
        ext = service_binary_config.get("ext", "tgz")
        return "." + ext

    @staticmethod
    def _is_nexus(service_binary_config):
        if "nexus" in service_binary_config:
            return True
        else:
        	return False    

