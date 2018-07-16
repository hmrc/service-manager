#!/usr/bin/env python
import json
import time
import re
from abc import abstractmethod

import requests

from servicemanager.smprocess import SmProcess, kill_pid
from servicemanager.service.smservice import SmService, SmMicroServiceStarter, SmServiceStatus
from servicemanager.smrepo import clone_repo_if_requred


class SmJvmServiceStarter(SmMicroServiceStarter):

    test_id_param = "service.manager.testId"

    def __init__(self, context, service_name, expected_service_type, run_from, port, classifier, service_mapping_ports, version, proxy, append_args):
        SmMicroServiceStarter.__init__(self, context, service_name, expected_service_type, run_from, port, classifier, service_mapping_ports, version, proxy, append_args)

    def start(self, appendArgs=None):
        if self.run_from == "SOURCE":
            if not clone_repo_if_requred(self):
                # TODO - should this just return None? or throw an exception?  Should clone_repo_if_required throw an exception?
                return None

            return self.start_from_sources()
        else:
            return self.start_from_binary()

    def process_arguments(self):
        run_from = self.run_from
        if self.run_from=="RELEASE":
            run_from = (self.version or "UNKNOWN") + "-" + run_from
        jvm_args = ["-Dservice.manager.serviceName=%s" % self.service_name]
        jvm_args += ["-Dservice.manager.runFrom=%s" % run_from]
        if self.context.is_test:
            jvm_args += ["-Dservice.manager.testId=%s" % self.context.test_id]
            jvm_args += ["-Dservice.manager.startTime=%s" % time.time()]
        return jvm_args

    @abstractmethod
    def start_from_sources(self):
        pass

    @abstractmethod
    def start_from_binary(self):
        pass


class SmJvmService(SmService):

    def __init__(self, context, service_name, expected_service_type):
        SmService.__init__(self, context, service_name, expected_service_type)
        self.pattern = "service.manager.serviceName=%s$" % self.service_name
        self.default_port = self.required_data("defaultPort")
        self.healthcheck = self.required_data("healthcheck")

    @abstractmethod
    def post_stop(self):
        pass

    @abstractmethod
    def get_port_argument(self):
        pass

    @abstractmethod
    def get_running_healthcheck_port(self, process):
        pass

    @abstractmethod
    def get_details_url(self):
        pass

    def get_pattern(self):
        return self.pattern

    def status(self, all_processes=None):
        processes = SmProcess.processes_matching(self.pattern, all_processes)

        def _status_for_process(process):
            port = process.extract_integer_argument('-D%s=(\d*)' % self.get_port_argument(), self.default_port)
            test_id = process.extract_argument('-Dservice.manager.testId=([^ ]+)', "")
            run_from = process.extract_argument('-Dservice.manager.runFrom=([^ ]+)', "")
            features = process.extract_arguments('-Dfeature.([^ =]+)=true', "")
            healthcheck = SmServiceStatus.HEALTHCHECK_PASS if self.run_healthcheck(process) else SmServiceStatus.HEALTHCHECK_BOOT
            return SmServiceStatus.for_process(self.service_name, process, port, test_id, run_from, features, healthcheck)

        return map(_status_for_process, processes)

    def request_running_service_details_on_default_port(self):
        url = self.get_details_url().replace("${port}", str(self.default_port))

        try:
            response = requests.get(url)
            return json.loads(response.text)
        except requests.RequestException:
            return None

    def is_started_on_default_port(self):
        processes = SmProcess.processes_matching(self.pattern)
        default_port_argument = "-D%s=%d" % (self.get_port_argument, self.default_port)

        for process in processes:
            if process.has_argument(default_port_argument):
                return True

        return False

    def get_default_healthcheck_port(self):
        return self.default_port

    def stop(self, wait=False):
        for process in SmProcess.processes_matching(self.pattern):
            kill_pid(self.context, process.ppid, wait=wait)
            kill_pid(self.context, process.pid, wait=wait)
            self.context.log("name: %s\tppid: %s\tpid: %s\tuptime: %s" % (self.service_name, process.ppid, process.pid, process.uptime), True)
        self.post_stop()

    def run_healthcheck(self, process):
        port = self.get_running_healthcheck_port(process)
        if not port:
            port = self.get_default_healthcheck_port()

        healthcheck_url = self.service_data["healthcheck"]["url"].replace("${port}", str(port))
        healthcheck_response_regex = self.service_data["healthcheck"]["response"] or ""

        try:
            ping_response = requests.get(healthcheck_url)
            response_text = ping_response.text
            return re.search(healthcheck_response_regex, response_text) and ping_response.status_code == 200
        except requests.RequestException:
            return False
