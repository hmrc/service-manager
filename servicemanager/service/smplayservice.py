#!/usr/bin/env python
import glob

import os
import re
import shutil
import zipfile
import tarfile
import stat
import copy
import types

from subprocess import Popen
from servicemanager.service.smservice import SmMicroServiceStarter
from servicemanager.service.smjvmservice import SmJvmService, SmJvmServiceStarter
from servicemanager.smfile import (
    force_chdir,
    remove_if_exists,
    remove_folder_if_exists,
    makedirs_if_not_exists,
)
from servicemanager.smartifactrepofactory import SmArtifactRepoFactory
from servicemanager.actions.colours import BColors

import subprocess


b = BColors()


class SmPlayServiceStarter(SmJvmServiceStarter):

    PLAY_PROCESS_STARTUP_TIMEOUT_SECONDS = 120

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
                extra_params += [
                    "-DDev.microservice.mongodb.uri=mongodb://localhost:27017/%s-%s"
                    % (self.context.database_name_prefix, self.service_name)
                ]

        if self.service_mapping_ports and self.service_data.get("hasServiceMappings", False):
            for dependent_service_name in self.service_mapping_ports:
                service_config_key_with_prefix = service_config_key
                if self.service_name == "FEGOVUK":
                    service_config_key_with_prefix = "govuk-tax.Dev.services"
                extra_params += [
                    "-D%s.%s.host=localhost" % (service_config_key_with_prefix, dependent_service_name),
                    "-D%s.%s.port=%d"
                    % (
                        service_config_key_with_prefix,
                        dependent_service_name,
                        self.service_mapping_ports[dependent_service_name],
                    ),
                ]

        if self.proxy:
            proxy_config = self.proxy.split(":")
            print("Starting service with proxy, '" + str(self.proxy) + "'")
            extra_params += [
                "-Dhttp.proxyHost=" + proxy_config[0],
                "-Dhttp.proxyPort=" + proxy_config[1],
            ]

        if self.append_args:
            if not isinstance(self.append_args, list):
                self.log(
                    "WARNING: I was passed a non list for append args of '"
                    + str(self.append_args)
                    + "' I dont know what to do with this"
                )
            else:
                extra_params += self.append_args

        return extra_params

    def __init__(
        self, context, service_name, run_from, port, classifier, service_mapping_ports, version, proxy, append_args,
    ):
        SmMicroServiceStarter.__init__(
            self,
            context,
            service_name,
            "play",
            run_from,
            port,
            classifier,
            service_mapping_ports,
            version,
            proxy,
            append_args,
        )

        if not self.port:
            self.port = self.service_data["defaultPort"]

    def supports_append_args(self):
        return True

    def get_start_command(self, run_from):
        if run_from == "SOURCE":
            source_cmd = copy.copy(self.service_data["sources"]["cmd"])
            source_cmd[-1] = source_cmd[-1] + " " + " ".join(self.sbt_extra_params())
            return source_cmd
        else:
            return self.service_data["binary"]["cmd"] + self._build_extra_params()

    def start_from_binary(self):
        microservice_target_path = self.context.get_microservice_target_path(self.service_name)
        force_chdir(microservice_target_path)

        binaryConfig = self.service_data["binary"]

        if not self.context.offline:
            artifactRepo = SmArtifactRepoFactory.get_repository(self.context, self.service_name, binaryConfig)
            if not self.version:
                self.version = artifactRepo.find_latest_version(
                    self.run_from, binaryConfig["artifact"], binaryConfig["groupId"]
                )
            artifactRepo.download_jar_if_necessary(self.run_from, self.version)

        unzip_dir = self._unpack_play_application(SmArtifactRepoFactory.get_play_app_extension(binaryConfig))
        parent, _ = os.path.split(unzip_dir)
        force_chdir(parent)

        if "frontend" in self.service_data and self.service_data["frontend"]:
            assets_versions = self._get_assets_version(unzip_dir)
            self.context.assets_versions_to_start(assets_versions)

        cmd_with_params = self.get_start_command("BINARY")
        if os.path.exists(cmd_with_params[0]):
            os.chmod(cmd_with_params[0], stat.S_IRWXU)
        else:
            self.context.log(
                b.fail + "ERROR: unable to chmod on non existent file '" + parent + cmd_with_params[0] + "'" + b.endc
            )

        makedirs_if_not_exists("logs")

        self.context.log(
            "Starting %s with parameters %s" % (self.service_name, cmd_with_params), True,
        )

        with open("logs/stdout.txt", "wb") as out, open("logs/stderr.txt", "wb") as err:
            popen_output = Popen(cmd_with_params, env=os.environ.copy(), stdout=out, stderr=err, close_fds=True,)
            if popen_output.returncode == 1:
                self.context.log(b.fail + "ERROR: could not start '" + self.service_name + "' " + b.endc)
            else:
                self.context.log("'%s' version '%s' started successfully" % (self.service_name, self.version))
            return popen_output.pid

    def _unpack_play_application(self, extension):
        service_data = self.service_data
        microservice_path = self.context.application.workspace + service_data["location"] + "/target/"
        force_chdir(microservice_path)
        microservice_filename = service_data["binary"]["artifact"] + extension

        unpacked_dir = SmPlayService.unzipped_dir_path(self.context, service_data["location"])
        remove_folder_if_exists(unpacked_dir)

        os.makedirs(unpacked_dir)

        if extension == ".zip":
            self._unzip_play_application(microservice_filename, unpacked_dir)
        elif extension == ".tgz":
            self._untar_play_application(microservice_filename, unpacked_dir)
        else:
            self.context.log("ERROR: unsupported atrifact extension: " + extension)

        folder = [name for name in os.listdir(unpacked_dir) if os.path.isdir(os.path.join(unpacked_dir, name))][0]
        target_dir = unpacked_dir + "/" + service_data["binary"]["destinationSubdir"]
        shutil.move(unpacked_dir + "/" + folder, target_dir)

        return target_dir

    def _unzip_play_application(self, zip_filename, unzipped_dir):
        zipfile.ZipFile(zip_filename, "r").extractall(unzipped_dir)

    def _untar_play_application(self, tgz_filename, unzipped_dir):
        tfile = tarfile.open(tgz_filename, "r:gz")
        tfile.extractall(unzipped_dir)

    def sbt_extra_params(self):
        sbt_extra_params = self._build_extra_params()

        if "extra_params" in self.service_data["sources"]:
            sbt_extra_params += self.service_data["sources"]["extra_params"]

        return sbt_extra_params

    def start_from_sources(self):
        sbt_extra_params = self.sbt_extra_params()

        service_data = self.context.service_data(self.service_name)
        microservice_path = self.context.application.workspace + service_data["location"]
        force_chdir(microservice_path)

        env_copy = os.environ.copy()
        env_copy["SBT_EXTRA_PARAMS"] = " ".join(sbt_extra_params)  # TODO: not needed i think anymore...

        makedirs_if_not_exists("logs")

        with open("logs/stdout.txt", "wb") as out, open("logs/stderr.txt", "wb") as err:
            process = Popen(
                self.get_start_command("SOURCE"), env=env_copy, stdout=out, stderr=err, stdin=subprocess.PIPE,
            )
            process.stdin.close()
            if process.returncode == 1:
                print(b.fail + "ERROR: could not start '" + self.service_name + "' " + b.endc)
            return process.pid  # Note: This is the parent pid

    def _get_assets_version(self, unzip_dir):
        assets_versions = []
        for conf_file in glob.glob(unzip_dir + "/conf/*.conf"):
            with open(conf_file, "r") as conf:
                conf = conf.read()
                conf_string = "".join(conf.split())
                pattern = re.compile(r'assets.*?version="([0-9.]*)"')
                new_assets_versions = re.findall(pattern, conf_string)

                assets_versions = assets_versions + new_assets_versions
        return list(set(assets_versions))


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
        return process.extract_integer_argument(r"-D%s=(\d*)" % self.get_port_argument(), self.default_port)
