import os
import sys
import urllib
import urllib2
import base64
import json

import requests

from servicemanager.smfile import remove_if_exists
from actions.colours import BColors
from smnexus import SmNexus


b = BColors()


class SmBintray():

    def __init__(self, context, service_name):
        self.context = context
        self.service_name = service_name
        self.service_type = context.service_type(service_name)


    def _resolve_credentials(self):
        return {'user': os.environ.get("BINTRAY_USER", ""), 'password': os.environ.get("BINTRAY_PASS", "")}
        
    def _header_credentials(self):
        credentials = self._resolve_credentials()
        return credentials["user"] + ":" + credentials["password"]

    def _get_version_info_from_bintray(self, artifact, repositoryId):
        url = self.context.config_value("bintray")["protocol"] + "://" + self.context.config_value("bintray")["apiHost"] + "/packages/" + repositoryId + "/" + artifact + "/versions/_latest"
        request = urllib2.Request(url)
        base64string = base64.encodestring(self._header_credentials()).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request).read()
        json_data = json.loads(response)
        return json_data["name"]

    def _get_version_files_from_bintray(self, artifact, repositoryId, version):
        url = self.context.config_value("bintray")["protocol"] + "://" + self.context.config_value("bintray")["apiHost"] + "/packages/" + repositoryId + "/" + artifact + "/versions/" + version + "/files"
        request = urllib2.Request(url)        
        base64string = base64.encodestring(self._header_credentials()).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request).read()
        json_data = json.loads(response)
        return json_data    

    def _find_tgz_file_path(self, version_files_json):
        tgzFiles = [element for element in version_files_json if element['name'].endswith(".tgz")]
        return tgzFiles[0]["path"]

    def _find_tgz_file_name(self, version_files_json):
        tgzFiles = [element for element in version_files_json if element['name'].endswith(".tgz")]
        return tgzFiles[0]["name"]   

    def _find_md5_file_path(self, version_files_json):
        tgzFiles = [element for element in version_files_json if element['name'].endswith(".tgz.md5")]
        return tgzFiles[0]["path"]   

    def find_latest_version(self, run_from, artifact):    
        version_env_var = None
        if "versionEnv" in self.context.service_data(self.service_name):
            version_env_var = self.context.service_data(self.service_name)["versionEnv"]

        try:
            version = os.environ[version_env_var]
        except Exception:
            repo_mappings = self.context.config_value("bintray")["repoMappings"]
            version = self._get_version_info_from_bintray(artifact, repo_mappings[run_from])
        return version

    def _download_from_bintray(self, bintray_path, local_filename, repositoryId, show_progress):
        url = self.context.config_value("bintray")["protocol"] + "://" + self.context.config_value("bintray")["downloadHost"] + "/" + repositoryId + "/" + bintray_path
        if show_progress:
            urllib.urlretrieve(url, local_filename, SmNexus._report_hook)
            print("\n")
        else:
            urllib.urlretrieve(url, local_filename)

    def download_jar_if_necessary(self, run_from, version):
        artifact = self.context.service_data(self.service_name)["binary"]["artifact"]
        repo_mappings = self.context.config_value("bintray")["repoMappings"]

        if not version:
            version = self.find_latest_version(run_from, artifact)

        files_json = self._get_version_files_from_bintray(artifact, repo_mappings[run_from], version)
        localFilename = artifact + ".tgz"
        bintrayFilePath = self._find_tgz_file_path(files_json)
        bintrayFilename = self._find_tgz_file_name(files_json)
        bintrayMD5FilePath = self._find_md5_file_path(files_json)
        microservice_target_path = self.context.get_microservice_target_path(self.service_name)
        downloaded_artifact_path = microservice_target_path + localFilename
        downloaded_md5_path = microservice_target_path + localFilename + ".md5"

        if version:   
             #first download the md5 file in order to determine if new artifact download is required
            self._download_from_bintray(bintrayMD5FilePath, downloaded_md5_path, repo_mappings[run_from], False)

            bintray_md5 = open(downloaded_md5_path, 'r').read()
            local_md5 = SmNexus._md5_if_exists(downloaded_artifact_path)

            if local_md5 != bintray_md5:
                remove_if_exists(downloaded_artifact_path)
                self.context.log("Downloading Bintray binary for '" + self.service_name + "': " + bintrayFilename)
                self._download_from_bintray(bintrayFilePath, downloaded_artifact_path, repo_mappings[run_from], self.context.show_progress)
            os.remove(downloaded_md5_path)
        else:
            print b.warning + "WARNING: Due to lack of version data from Bintray you may not have an up to date version..." + b.endc    