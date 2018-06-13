import os
import sys
import time
import urllib
import hashlib
import urllib2
import base64
from xml.dom.minidom import parse

import requests

from servicemanager.smfile import remove_if_exists
from actions.colours import BColors


b = BColors()


class SmNexus():

    def __init__(self, context, service_name):
        self.context = context
        self.service_name = service_name
        self.service_type = context.service_type(service_name)

    @staticmethod
    def _report_hook(count, block_size, total_size):
        global start_time
        global last_update

        current_milli_time = lambda: int(time.time() * 1000)

        if count == 0:
            start_time = time.time()
            last_update = current_milli_time()
            return
        duration = time.time() - start_time
        progress_size = int(count * block_size)
        try:
            speed = int(progress_size / (1024 * duration))
        except ZeroDivisionError:
            speed = 0

        percent = int(count * block_size * 100 / total_size)
        if percent == 100 or (current_milli_time()  - last_update) > 500:
            sys.stdout.write("\r%d%%, %d MB, %d KB/s, %d seconds passed" %
                         (percent, progress_size / (1024 * 1024), speed, duration))
            sys.stdout.flush()
            last_update = current_milli_time()

    def _create_nexus_extension(self):
        if self.service_type == "play":
            ext = self.context.service_data(self.service_name)["binary"].get('ext', 'tgz')
            return "." + ext
        elif self.service_type == "assets":
            return ".zip"
        else:
            return "-shaded.jar"

    @staticmethod
    def _md5_if_exists(path):
        if os.path.exists(path):
            return hashlib.md5(open(path, 'rb').read()).hexdigest()
        else:
            return 0

    def resolve_credentials(self):
        return self.context.credentials.resolve_nexus_credentials()

    def _header_credentials(self):
        credentials = self.resolve_credentials()
        return credentials["user"] + ":" + credentials["password"]

    def _url_credentials(self):
        credentials = self.resolve_credentials()
        return urllib.quote_plus(credentials['user']) + ":" + urllib.quote_plus(credentials["password"])

    def _download_from_nexus(self, nexus_path, shaded_jar, show_progress):
        url = self._get_protocol() + "://" + self._url_credentials() + "@" + nexus_path
        if show_progress:
            urllib.urlretrieve(url, shaded_jar, SmNexus._report_hook)
            print("\n")
        else:
            urllib.urlretrieve(url, shaded_jar)

    def _is_valid_repository(self, repository, data):
        repository_id = data.getElementsByTagName("latest" + repository + "RepositoryId")[0].firstChild.nodeValue
        repo_mappings = self.context.config_value("nexus")["repoMappings"]
        if not repository_id in repo_mappings.values():
            self.context.log("The repositoryId " + repository_id + " is not in: " + str(repo_mappings.values()))
            sys.exit(-1)

    def _find_version_in_dom(self, repository, dom):
        latest = "latest" + repository
        try:
            data = dom.getElementsByTagName("artifact")[0]
        except:
            self.context.log("Unable to get latest version from nexus")
            return None

        self._is_valid_repository(repository, data)
        return data.getElementsByTagName(latest)[0].firstChild.nodeValue

    def _find_all_versions_in_dom(self, repository, dom):
        try:
            data = dom.getElementsByTagName("artifact")
        except:
            self.context.log("Unable to get artifacts from nexus")
            return None

        versions = []
        for element in data:
            self._is_valid_repository(repository, element)
            version = element.getElementsByTagName("version")[0].firstChild.nodeValue
            versions.append(version)
        return versions

    def _get_protocol(self):
        protocol = "https"
        if "protocol" in self.context.config_value("nexus"):
            protocol = self.context.config_value("nexus")["protocol"]
        return protocol

    def _get_version_info_from_nexus(self, artifact, repository_id):
        lucene_nexus = self._get_protocol() + "://" + self.context.config_value("nexus")["host"] + "/service/local/lucene/search?a=" + artifact + "&repositoryId=" + repository_id
        request = urllib2.Request(lucene_nexus)
        base64string = base64.encodestring(self._header_credentials()).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request)
        dom = parse(response)
        response.close()
        return dom

    def find_latest_version(self, run_from, artifact, groupId):
        if run_from == "RELEASE":
            repository = "Release"
        else:
            repository = "Snapshot"

        version_env_var = None
        if "versionEnv" in self.context.service_data(self.service_name):
            version_env_var = self.context.service_data(self.service_name)["versionEnv"]

        try:
            version = os.environ[version_env_var]
        except Exception:
            repo_mappings = self.context.config_value("nexus")["repoMappings"]
            dom = self._get_version_info_from_nexus(artifact, repo_mappings[run_from])
            version = self._find_version_in_dom(repository, dom)
        return version

    def get_all_versions(self, run_from):
        binary = self.context.service_data(self.service_name)["binary"]
        if run_from == "RELEASE":
            repository = "Release"
        else:
            repository = "Snapshot"
        repo_mappings = self.context.config_value("nexus")["repoMappings"]
        dom = self._get_version_info_from_nexus(binary["artifact"], repo_mappings[run_from])
        versions = self._find_all_versions_in_dom(repository, dom)
        return versions

    def download_jar_if_necessary(self, run_from, version):
        binary = self.context.service_data(self.service_name)["binary"]
        nexus_host = self.context.application.nexus_repo_host
        artifact = binary["artifact"]
        group_id = binary["groupId"]

        filename = self.context.get_jar_filename(self.service_name, run_from)
        microservice_target_path = self.context.get_microservice_target_path(self.service_name)

        repo_mappings = self.context.config_value("nexus")["repoMappings"]
        if run_from == "RELEASE":
            url_type_repository = repo_mappings["RELEASE"]
        else:
            url_type_repository = repo_mappings["SNAPSHOT"]

        if not version:
            version = self.find_latest_version(run_from, artifact, group_id)

        if version:
            nexus_extension = self._create_nexus_extension()
            nexus_filename = artifact + "-" + version + nexus_extension
            md5_filename = nexus_filename + ".md5"
            nexus_url = nexus_host + binary["nexus"] + url_type_repository + "/" + group_id + artifact + "/" + version + "/"
            # first download the md5 file in order to determine if new artifact download is required
            self._download_from_nexus(nexus_url + md5_filename, microservice_target_path + md5_filename, False)
            if self.service_type == "assets":
                if self._md5_if_exists(microservice_target_path + nexus_filename) != open(microservice_target_path + md5_filename, 'r').read():
                    remove_if_exists(microservice_target_path + filename)
                    self.context.log("Downloading Nexus binary for '" + self.service_name + "': " + nexus_filename)
                    self._download_from_nexus(nexus_url + nexus_filename, nexus_filename, self.context.show_progress)
            else:
                if self._md5_if_exists(microservice_target_path + filename) != open(microservice_target_path + md5_filename, 'r').read():
                    remove_if_exists(microservice_target_path + filename)
                    self.context.log("Downloading Nexus binary for '" + self.service_name + "': " + nexus_filename)
                    self._download_from_nexus(nexus_url + nexus_filename, filename, self.context.show_progress)
            os.remove(microservice_target_path + md5_filename)
        else:
            print b.warning + "WARNING: Due to lack of version data from nexus you may not have an up to date version..." + b.endc
