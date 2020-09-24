#!/usr/bin/env python
import os
import shutil
import zipfile
import signal
import time
import re
import sys

import requests

import subprocess
from .smservice import SmService, SmMicroServiceStarter, SmServiceStatus
from servicemanager.smprocess import SmProcess, kill_pid
from servicemanager.smfile import (
    force_chdir,
    remove_if_exists,
    remove_folder_if_exists,
    makedirs_if_not_exists,
)
from servicemanager.smartifactory import SmArtifactory
from servicemanager.smrepo import clone_repo_if_requred


def _is_python_3():
    proc = subprocess.Popen(["python", "--version"],
                          shell=False,
                          env=os.environ.copy(),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          close_fds=True,
                          universal_newlines=True)
    pyver = proc.stdout.readline().lower()
    return pyver.startswith("python 3")

class SmPythonServiceStarter(SmMicroServiceStarter):

    PROCESS_STARTUP_TIMEOUT_SECONDS = 90

    def __init__(
        self,
        context,
        service_name,
        run_from,
        port,
        classifier,
        service_mapping_ports,
        version,
        proxy=None,
        append_args=None,
    ):
        SmMicroServiceStarter.__init__(
            self,
            context,
            service_name,
            "assets",
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

    def process_arguments(self):
        pass

    def get_start_command(self, run_from):
        return self.service_data["binary"]["cmd"]

    def _start_from_binary(self):
        assets_target_path = self.context.get_microservice_target_path(self.service_name)
        assets_path = self.context.application.workspace + self.service_data["location"]

        force_chdir(assets_path)
        remove_if_exists("RUNNING_FROM")

        force_chdir(assets_target_path)

        if not self.context.offline:
            artifactory = SmArtifactory(self.context, self.service_name)

            if self.version:
                versions = [self.version]
            elif self.context.assets_versions:
                versions = self.context.assets_versions
                self.log("Starting assets versions: %s" % (", ".join(versions)), True)
            else:
                versions = artifactory.find_all_versions(self.run_from)
                self.log("Starting assets versions: %s" % (", ".join(versions)), True)

            for version in versions:
                self.context.log("\nStarting assets version: %s" % version)
                artifactory.download_jar_if_necessary(self.run_from, version)
            self._unzip_assets(versions)

        cmd_with_params = self.service_data["binary"]["cmd"]
        if _is_python_3():
            py3cmd = self.service_data["binary"].get("py3_cmd")
            if py3cmd is not None:
                cmd_with_params = py3cmd

        self.log("starting %s..." % cmd_with_params)

        makedirs_if_not_exists("logs")
        with open("logs/stdout.txt", "wb") as out, open("logs/stderr.txt", "wb") as err:
            return subprocess.Popen(
                cmd_with_params[0].split(),
                shell=False,
                env=os.environ.copy(),
                stdout=out,
                stderr=err,
                close_fds=True,
                universal_newlines=True,
            ).pid

    def _start_from_sources(self):

        service_data = self.context.service_data(self.service_name)
        assets_path = self.context.application.workspace + service_data["location"]

        cmd_with_params = self.service_data["sources"]["cmd"]
        force_chdir(assets_path)
        run_from_file = open("RUNNING_FROM", "w")
        run_from_file.write(self.run_from)
        run_from_file.close()

        makedirs_if_not_exists("logs")
        seconds_remaining = SmPythonServiceStarter.PROCESS_STARTUP_TIMEOUT_SECONDS

        with open("logs/stdout.txt", "wb") as out, open("logs/stderr.txt", "wb") as err:
            subprocess.Popen(
                cmd_with_params, shell=False, env=os.environ.copy(), stdout=out, stderr=err, close_fds=True,
            )

        while seconds_remaining > 0 and not len(SmProcess.processes_matching("grunt")) > 0:
            time.sleep(1)
            seconds_remaining -= 1
            if seconds_remaining < 10 or seconds_remaining % 5 == 0:
                self.log(
                    "Waiting for Assets service to start: %s second%s before timeout"
                    % (seconds_remaining, "s" if seconds_remaining > 1 else "")
                )
        if len(SmProcess.processes_matching("grunt")) == 1:
            process = SmProcess.processes_matching("grunt")
            for i, v in enumerate(process):
                return v.pid

    def _unzip_assets(self, versions):
        service_data = self.service_data
        assets_zip_path = self.context.get_microservice_target_path(self.service_name)
        force_chdir(assets_zip_path)
        unzipped_dir = "assets"
        if not os.path.exists(unzipped_dir):
            os.makedirs(unzipped_dir)

        for version in versions:
            zip_filename = service_data["binary"]["artifact"] + "-" + version + ".zip"
            extracted_dir = version
            if not os.path.exists(assets_zip_path + "/assets/" + extracted_dir):
                os.makedirs(extracted_dir)
                zipfile.ZipFile(zip_filename, "r").extractall(extracted_dir)
                shutil.move(extracted_dir, unzipped_dir)
        target_dir = unzipped_dir
        return target_dir

    def start(self):
        if self.run_from == "SOURCE" and "sources" in self.service_data:
            if not clone_repo_if_requred(self):
                # TODO - should this just return? or throw an exception, or return None explicitly?
                return

            return self._start_from_sources()
        else:
            return self._start_from_binary()


class SmPythonService(SmService):
    @staticmethod
    def unzipped_dir_path(context, location):
        return context.application.play_extraction_dir + location + "_" + context.instance_id

    def __init__(self, context, service_name):

        SmService.__init__(self, context, service_name, "assets")
        self.default_port = self.required_data("defaultPort")
        self.healthcheck = self.required_data("healthcheck")
        self.pattern = SmPythonService.get_pattern(self)

    def stop(self, wait=False):

        procs = SmProcess.processes_matching(SmPythonService.get_pattern(self), None)

        if len(procs) == 0:
            return

        self.log("Stopping '%s'..." % (self.service_data["name"]), True)

        for proc in procs:
            kill_pid(self.context, proc.pid, wait=wait)
            self.log("PID  %d killed" % proc.pid, True)

    def clean_up(self):
        unzip_path = SmPythonService.unzipped_dir_path(self.context, self.service_data["location"])
        remove_folder_if_exists(unzip_path)

    def request_running_service_details_on_default_port(self):
        # TODO: implement git revision stuff for python or remove the feature
        return None

    def status(self, all_processes=None):
        processes = SmProcess.processes_matching(SmPythonService.get_pattern(self), all_processes)

        if len(processes) == 0:
            return []

        if len(processes) > 1:
            self.log("POSSIBLE PROBLEM: Found more than one process")

        def _status_for_process(process):
            healthcheck = (
                SmServiceStatus.HEALTHCHECK_PASS if self.run_healthcheck(None) else SmServiceStatus.HEALTHCHECK_BOOT
            )
            return SmServiceStatus.for_process(self.service_name, process, self.default_port, "", "", "", healthcheck)

        return list(map(_status_for_process, processes))

    def run_healthcheck(self, process):
        port = self.default_port

        healthcheck_url = self.service_data["healthcheck"]["url"].replace("${port}", str(port))

        healthcheck_response_regex = self.service_data["healthcheck"]["response"]
        try:
            ping_response = requests.get(healthcheck_url)
            response_text = str(ping_response.status_code)
            return re.search(healthcheck_response_regex, response_text) is not None
        except requests.RequestException:
            return False

    def is_started_on_default_port(self):
        return len(SmProcess.processes_matching(SmPythonService.get_pattern(self))) > 0

    def get_pattern(self):
        if _is_python_3():
            return self.service_data.get("py3_pattern")
        else:
            return self.service_data["pattern"]
