#!/usr/bin/env python
import os
import re

import requests
import types

from servicemanager.service.smservice import SmServiceStarter, SmService, SmServiceStatus
from servicemanager.smprocess import SmProcess, kill_processes_matching
from servicemanager import subprocess


class SmExternalServiceStarter(SmServiceStarter):

    def process_arguments(self):
        pass

    def __init__(self, context, service_name, append_args):
        SmServiceStarter.__init__(self, context, service_name, "external", append_args)
        if not "cmd" in self.service_data:
            context.log("Could not start 'external' service '" + service_name + "', 'cmd' is missing from services.json")
        self.cmd = self.service_data["cmd"]

    def get_start_command(self, context=None):
        if self.append_args:
            if isinstance(self.append_args, types.ListType):
                return self.cmd + self.append_args
            else:
                return self.cmd
                self.log("WARNING: I was passed a non list for append args of '" + str(self.append_args) + "' I dont know what to do with this")
        else:
            return self.cmd

    def supports_append_args(self):
        return True

    def start(self):
        try:
            location = "."
            if "location" in self.service_data:
                location = self.service_data["location"]
            microservice_path = os.path.join(self.context.application.workspace, location)
            os.chdir(microservice_path)

            return subprocess.Popen(self.get_start_command(), cwd=microservice_path, env=os.environ.copy(), shell=False).pid
        except Exception, e:
            self.log("Could not start service due to exception: " + str(e))


class SmExternalService(SmService):

    def __init__(self, context, service_name):
        SmService.__init__(self, context, service_name, "external")
        self.pattern = self.required_data("pattern")

    def get_pattern(self):
        return self.pattern

    def stop(self, wait=False):
        kill_processes_matching(self.pattern, self.context, wait == True, wait)

    def clean_up(self):
        pass

    def is_started_on_default_port(self):
        return len(SmProcess.processes_matching(self.pattern)) > 0

    def request_running_service_details_on_default_port(self):
        return None

    def run_healthcheck(self, port=None):
        if "healthcheck" in self.service_data:
            healthcheck_url = self.service_data["healthcheck"]["url"]
            healthcheck_response_regex = self.service_data["healthcheck"]["response"]

            try:
                ping_response = requests.get(healthcheck_url)
                response_text = ping_response.text
                return re.search(healthcheck_response_regex, response_text) is not None
            except requests.RequestException:
                return False
        else:
            return None

    def status(self, all_processes=None):
        processes = SmProcess.processes_matching(self.pattern, all_processes)

        if len(processes) == 0:
            return []

        if len(processes) > 1:
            self.log("POSSIBLE PROBLEM: Found more than one process")

        def _status_for_process(process):
            hc_result = self.run_healthcheck(process)
            healthcheck = SmServiceStatus.HEALTHCHECK_NONE
            if hc_result is not None:
                healthcheck = SmServiceStatus.HEALTHCHECK_PASS if self.run_healthcheck(process) else SmServiceStatus.HEALTHCHECK_BOOT
            return SmServiceStatus.for_process(self.service_name, process, "", "", "", "", healthcheck)


        return map(_status_for_process, processes)
