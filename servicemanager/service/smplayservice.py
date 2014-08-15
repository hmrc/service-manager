#!/usr/bin/env python

import os
import shutil
import zipfile
import stat
import time
import json
import copy

from servicemanager.subprocess import Popen
from ..service.smservice import SmMicroServiceStarter
from smjvmservice import SmJvmService, SmJvmServiceStarter
from ..smfile import force_chdir, force_pushdir, remove_if_exists, remove_folder_if_exists, makedirs_if_not_exists
from ..smnexus import SmNexus
from ..actions.colours import BColors

from servicemanager import subprocess


b = BColors()


class SmPlayServiceStarter(SmJvmServiceStarter):

    PLAY_PROCESS_STARTUP_TIMEOUT_SECONDS = 120

    def __init__(self, context, service_name, run_from, port, classifier, service_mapping_ports, version, proxy):
        SmMicroServiceStarter.__init__(self, context, service_name, "play", run_from, port, classifier, service_mapping_ports, version, proxy)

        if not self.port:
            self.port = self.service_data["defaultPort"]

    def _build_extra_params(self):
        extra_params = ["-Dhttp.port=%d" % self.port]
        extra_params += self.process_arguments()
        # Features are so specific - should this be in config?
        if self.context.features:
            for feature in self.context.features:
                extra_params += ["-Dfeature.%s=true" % feature]

        service_config_key = "Dev.microservice.services"

        if self.context.is_test:
            if self.service_data.get("hasMongo", False):
                extra_params += ["-DDev.microservice.mongodb.uri=mongodb://localhost:27017/%s-%s" % (self.context.database_name_prefix, self.service_name)]

        if self.service_mapping_ports and self.service_data.get("hasServiceMappings", False):
            for dependent_service_name in self.service_mapping_ports:
                service_config_key_with_prefix = service_config_key
                if self.service_name == "FEGOVUK":
                    service_config_key_with_prefix = "govuk-tax.Dev.services"
                extra_params += [
                    "-D%s.%s.host=localhost" % (service_config_key_with_prefix, dependent_service_name),
                    "-D%s.%s.port=%d" % (service_config_key_with_prefix, dependent_service_name, self.service_mapping_ports[dependent_service_name])
                ]

        if self.proxy:
            proxy_config = self.proxy.split(":")
            print "Starting service with proxy, '" + str(self.proxy) + "'"
            extra_params += [
                "-Dhttp.proxyHost=" + proxy_config[0],
                "-Dhttp.proxyPort=" + proxy_config[1]
            ]

        return extra_params

    def get_start_command(self, run_from):
        if run_from == "SOURCE":
            source_cmd = copy.copy(self.service_data["sources"]["cmd"])
            source_cmd[-1] = source_cmd[-1] + " " +  " ".join(self.sbt_extra_params())
            return source_cmd
        else:
            return self.service_data["binary"]["cmd"] + self._build_extra_params()

    def start_from_binary(self):
        microservice_target_path = self.context.get_microservice_target_path(self.service_name)
        force_chdir(microservice_target_path)

        if not self.context.offline:
            nexus = SmNexus(self.context, self.service_name)
            nexus.download_jar_if_necessary(self.run_from, self.version)

        unzip_dir = self._unzip_play_application()
        parent, _ = os.path.split(unzip_dir)
        force_pushdir(parent)

        cmd_with_params = self.get_start_command("BINARY")
        if os.path.exists(cmd_with_params[0]):
            os.chmod(cmd_with_params[0], stat.S_IRWXU)
        else:
            print b.fail + "ERROR: unable to chmod on non existent file '" + parent + cmd_with_params[0] + "'" + b.endc

        makedirs_if_not_exists("logs")

        print(cmd_with_params)

        with open("logs/stdout.txt", "wb") as out, open("logs/stderr.txt", "wb") as err:
            popen_output = Popen(cmd_with_params, env=os.environ.copy(), stdout=out, stderr=err, close_fds=True)
            if popen_output.returncode == 1:
                print b.fail + "ERROR: could not start '" + self.service_name + "' " + b.endc
            return popen_output.pid

    def _unzip_play_application(self):
        service_data = self.service_data
        microservice_zip_path = self.context.application.workspace + service_data["location"] + "/target/"
        force_pushdir(microservice_zip_path)
        zip_filename = service_data["binary"]["artifact"] + ".zip"

        unzipped_dir = SmPlayService.unzipped_dir_path(self.context, service_data["location"])
        remove_folder_if_exists(unzipped_dir)

        os.makedirs(unzipped_dir)
        zipfile.ZipFile(zip_filename, 'r').extractall(unzipped_dir)

        folder = os.listdir(unzipped_dir)[0]
        target_dir = unzipped_dir + "/" + service_data["binary"]["destinationSubdir"]
        shutil.move(unzipped_dir + "/" + folder, target_dir)

        return target_dir

    def sbt_extra_params(self):
        sbt_extra_params = self._build_extra_params()

        if "extra_params" in self.service_data["sources"]:
            sbt_extra_params += self.service_data["sources"]["extra_params"]

        return sbt_extra_params

    def start_from_sources(self):
        sbt_extra_params = self.sbt_extra_params()

        service_data = self.context.service_data(self.service_name)
        microservice_path = self.context.application.workspace + service_data["location"]
        curr_dir = force_pushdir(microservice_path)

        env_copy = os.environ.copy()
        env_copy["SBT_EXTRA_PARAMS"] = " ".join(sbt_extra_params) # TODO: not needed i think anymore...

        makedirs_if_not_exists("logs")

        with open("logs/stdout.txt", "wb") as out, open("logs/stderr.txt", "wb") as err:
            process = Popen(self.get_start_command("SOURCE"), env=env_copy, stdout=out, stderr=err, stdin=subprocess.PIPE)
            process.stdin.close()
            if process.returncode == 1:
                print b.fail + "ERROR: could not start '" + self.service_name + "' " + b.endc
            return process.pid # Note: This is the parent pid


class SmPlayService(SmJvmService):

    @staticmethod
    def unzipped_dir_path(context, location):
        return context.application.play_extraction_dir + location + "_" + context.instance_id

    def __init__(self, context, service_name):
        SmJvmService.__init__(self, context, service_name, "play")
        self.default_port = self.required_data("defaultPort")
        self.healthcheck = self.required_data("healthcheck")

    def post_stop(self):
        pass

    def clean_up(self):
        unzip_path = SmPlayService.unzipped_dir_path(self.context, self.service_data["location"])
        remove_folder_if_exists(unzip_path)

    def get_details_url(self):
        return "http://localhost:${port}/admin/details"

    def get_port_argument(self):
        return "http.port"

    def get_running_healthcheck_port(self, process):
        return process.extract_integer_argument('-D%s=(\d*)' % self.get_port_argument(), self.default_port)
