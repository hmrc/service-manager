import os
import sys
import urllib
import urllib2
import base64
import requests

from servicemanager.smfile import remove_if_exists
from actions.colours import BColors
from smnexus import SmNexus
from xml.dom.minidom import parse


b = BColors()


class SmBintray():

    def __init__(self, context, service_name):
        self.context = context
        self.service_name = service_name
        self.service_type = context.service_type(service_name)
   
    def _find_latest_in_dom(self, dom):
        try:
            data = dom.getElementsByTagName("versioning")[0]
        except:
            self.context.log("Unable to get latest version from bintray")
            return None

        latestVersion =  data.getElementsByTagName("latest")[0].firstChild.nodeValue
        return latestVersion

    def _get_version_info_from_bintray(self, artifact, repositoryId, groupId):
        url = self.context.config_value("bintray")["protocol"] + "://" + self.context.config_value("bintray")["host"] + "/" + repositoryId + "/" + groupId + artifact + "/maven-metadata.xml"
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        dom = parse(response)
        response.close()
        return self._find_latest_in_dom(dom)

    def find_latest_version(self, run_from, artifact, groupId):    
        version_env_var = None
        if "versionEnv" in self.context.service_data(self.service_name):
            version_env_var = self.context.service_data(self.service_name)["versionEnv"]

        try:
            version = os.environ[version_env_var]
        except Exception:
            repo_mappings = self.context.config_value("bintray")["repoMappings"]
            version = self._get_version_info_from_bintray(artifact, repo_mappings[run_from], groupId)
        return version

    def _download_from_bintray(self, bintray_path, local_filename, repositoryId, show_progress):
        url = self.context.config_value("bintray")["protocol"] + "://" + self.context.config_value("bintray")["host"] + "/" + repositoryId + "/" + bintray_path
        if show_progress:
            urllib.urlretrieve(url, local_filename, SmNexus._report_hook)
            print("\n")
        else:
            urllib.urlretrieve(url, local_filename)

    def download_jar_if_necessary(self, run_from, version):
        artifact = self.context.service_data(self.service_name)["binary"]["artifact"]
        groupId = self.context.service_data(self.service_name)["binary"]["groupId"]
        repo_mappings = self.context.config_value("bintray")["repoMappings"]
        repositoryId = repo_mappings[run_from]

        if not version:
            version = self.find_latest_version(run_from, artifact, groupId)

        if version:
            localFilename = artifact + ".tgz"
            bintrayFilename = artifact + "-" + str(version) + ".tgz"
            bintrayFilePath = groupId + artifact + "/" + str(version) + "/" + bintrayFilename
            bintrayMD5FilePath = bintrayFilePath + ".md5"
            microservice_target_path = self.context.get_microservice_target_path(self.service_name)
            downloaded_artifact_path = microservice_target_path + localFilename
            downloaded_md5_path = microservice_target_path + localFilename + ".md5"

             # first download the md5 file in order to determine if new artifact download is required
            self._download_from_bintray(bintrayMD5FilePath, downloaded_md5_path, repositoryId, False)

            bintray_md5 = open(downloaded_md5_path, 'r').read()
            local_md5 = SmNexus._md5_if_exists(downloaded_artifact_path)

            if local_md5 != bintray_md5:
                remove_if_exists(downloaded_artifact_path)
                self.context.log("Downloading Bintray binary for '" + self.service_name + "': " + bintrayFilename)
                self._download_from_bintray(bintrayFilePath, downloaded_artifact_path, repositoryId, self.context.show_progress)
            os.remove(downloaded_md5_path)
        else:
            print b.warning + "WARNING: Due to lack of version data from Bintray you may not have an up to date version..." + b.endc    