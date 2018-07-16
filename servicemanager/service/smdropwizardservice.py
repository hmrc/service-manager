#!/usr/bin/env python

import os

from servicemanager.subprocess import Popen
from servicemanager.smfile import force_chdir
from servicemanager.smnexus import SmNexus
from servicemanager.service.smservice import SmMicroServiceStarter
from smjvmservice import SmJvmService, SmJvmServiceStarter
from servicemanager.actions.colours import BColors

b = BColors()


class SmDropwizardServiceStarter(SmJvmServiceStarter):

    DEV_NULL = open(os.devnull, 'w')

    def __init__(self, context, service_name, run_from, port, admin_port, classifier, service_mapping_ports, version, proxy, append_args=None):
        SmMicroServiceStarter.__init__(self, context, service_name, "dropwizard", run_from, port, classifier, service_mapping_ports, version, proxy, append_args)

        self.admin_port = admin_port

        self.java_options = [
            "-Dfile.encoding=UTF8",
            "-Xmx64M",
            "-XX:+CMSClassUnloadingEnabled",
            "-XX:MaxPermSize=64m"
        ]

        self.java_home = context.application.java_home

    def _get_jar_filename(self):
        return self.context.get_jar_filename(self.service_name, self.run_from)

    def _get_binary_start_cmd(self):
        binary_data = self.service_data["binary"]
        filename = self._get_jar_filename()

        if "configurationFile" not in binary_data:
            print "ERROR: required config 'configurationFile' does not exist"
            return None

        configuration_file = binary_data["configurationFile"]
        output_configuration_file = os.path.join(self.run_from, configuration_file)
        microservice_target_path = self.context.get_microservice_target_path(self.service_name)
        _java_bin = os.path.join(self.java_home, os.path.join("bin", "java"))
        extra_params = self._build_extra_params()
        cmd = [_java_bin] + self.java_options + extra_params
        os.path.join(microservice_target_path, filename)
        return cmd + ["-jar",  microservice_target_path + filename, "server", microservice_target_path + output_configuration_file]


    def get_start_command(self, run_from):
        if run_from == "SOURCE":
            return self.sources["cmd"]
        else:
            return self._get_binary_start_cmd()

    def start_from_binary(self):

        microservice_target_path = self.context.get_microservice_target_path(self.service_name)
        force_chdir(microservice_target_path)

        if not self.context.offline:
            nexus = SmNexus(self.context, self.service_name)
            nexus.download_jar_if_necessary(self.run_from, self.version)

        filename = self._get_jar_filename()

        service_data = self.service_data
        binary_data = service_data["binary"]

        if "configurationFile" in binary_data:
            configuration_file = binary_data["configurationFile"]
        else:
            print "ERROR: required config 'configurationFile' does not exist"
            return None

        binary_to_run = os.path.join(microservice_target_path, filename)
        if os.path.exists(binary_to_run):
            force_chdir(self.run_from)
            os.system("jar xvf " + microservice_target_path + filename + " " + configuration_file + " > /dev/null")
            force_chdir(microservice_target_path)
            cmd = self.get_start_command("BINARY")
            process = Popen(cmd, env=os.environ.copy(), stdout=SmDropwizardServiceStarter.DEV_NULL, stderr=SmDropwizardServiceStarter.DEV_NULL, close_fds=True)
            if process.returncode == 1:
                print b.fail + "ERROR: could not start '" + self.service_name + "' " + b.endc
            else:
                self.context.log("'%s' version '%s' started successfully" % (self.service_name, self.version))
            return process.pid
        else:
            print "ERROR: the requested file: '" + binary_to_run + "' does not exist"
            return None

    def _build_extra_params(self):

        extra_params = [
            "-Ddw.http.port=%d" % self.port,
            "-Dservice.manager.serviceName=" + self.service_name
        ]
        extra_params += self.process_arguments()

        # Features are so specific - should this be in config?
        if self.context.features:
            for feature in self.context.features:
                extra_params += ["-Dfeature.%s=true" % feature]

        if self.admin_port:
            extra_params += ["-Ddw.http.adminPort=%d" % self.admin_port]

        if self.context.is_test:
            if self.service_data.get("hasMongo", False):
                extra_params += ["-Ddw.mongodb.db=%s-%s" % (self.context.database_name_prefix, self.service_name)]

        if self.service_mapping_ports and self.service_data.get("hasServiceMappings", False):
            for dependent_service_name in self.service_mapping_ports:
                extra_params += ["-Ddw.serviceMappings." + dependent_service_name + ".port=" + str(self.service_mapping_ports[dependent_service_name])]

        return extra_params

    def start_from_sources(self):

        sbt_extra_params = self._build_extra_params()

        base_dir = self.context.application.workspace + self.service_data["location"]
        cmd = self.sources["cmd"]

        process = None
        try:
            new_env = os.environ.copy()
            # SBT is so specific should this be in configuration?
            new_env["SBT_EXTRA_PARAMS"] = " ".join(sbt_extra_params)
            os.chdir(base_dir)
            process = Popen(self.get_start_command("SOURCE"), env=new_env, stdout=SmDropwizardServiceStarter.DEV_NULL, stderr=SmDropwizardServiceStarter.DEV_NULL, close_fds=True)
        except Exception, e:
            self.log("Could not start service in '%s' due to exception: %s" % (base_dir, str(e)))

        return process.pid


class SmDropwizardService(SmJvmService):

    def __init__(self, context, service_name):
        SmJvmService.__init__(self, context, service_name, "dropwizard")
        self.default_admin_port = self.required_data("defaultAdminPort")

    def clean_up(self):
        pass

    def post_stop(self):
        pass

    def get_details_url(self):
        return "http://localhost:${port}/ping/details"

    def get_port_argument(self):
        return "dw.http.port"

    def get_running_healthcheck_port(self, process):
        return process.extract_integer_argument('-Ddw.http.adminPort=(\d*)', self.default_admin_port)
