#!/usr/bin/env python

import os
import json
import time
import sys
import collections
import copy

from pymongo import MongoClient

from smcredentials import CredentialsResolver
from smprocess import kill_by_test_id, test_has_running_processes, SmProcess
from servicemanager.service.smplayservice import SmPlayService, SmPlayServiceStarter
from service.smdropwizardservice import SmDropwizardService, SmDropwizardServiceStarter
from service.smexternalservice import SmExternalService, SmExternalServiceStarter
from service.smpythonservice import SmPythonServiceStarter, SmPythonService
from smutil import pretty_print_list, if_not, unify_lists
from actions.colours import BColors

b = BColors()


def validate_run_from(value):
    if value in ["RELEASE", "SNAPSHOT", "SOURCE"]:
        return True
    return False


def merge_dict(d1, d2):
    """
    Modifies d1 in-place to contain values from d2.  If any value
    in d1 is a dictionary (or dict-like), *and* the corresponding
    value in d2 is also a dictionary, then merge them in-place.
    """
    for k,v2 in d2.items():
        v1 = d1.get(k) # returns None if v1 has no value for this key
        if ( isinstance(v1, collections.Mapping) and
             isinstance(v2, collections.Mapping) ):
            merge_dict(v1, v2)
        else:
            d1[k] = v2


class ServiceManagerException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class SmApplication():
    # Application context object - loads, validates and stores global configuration

    def __init__(self, configuration_dir_parameter=None, features=None, process_manager=SmProcess):

        self.workspace = SmApplication._required_environment_directory("WORKSPACE", "your workspace root dir")
        self.java_home = SmApplication._required_environment_directory("JAVA_HOME", "path/to/jdk")

        self.configuration_dir = SmApplication._get_configuration_dir(self, configuration_dir_parameter)

        self.services = SmApplication._read_json_config(self, "services.json")
        self.profiles = SmApplication._read_json_config(self, "profiles.json")
        self.config = SmApplication._read_json_config(self, "config.json")

        self.templates = SmApplication._read_json_config(self, "templates.json")
        self.merge_template_config()

        self.nexus_repo_host = SmApplication._read_json_config(self, "config.json")["nexus"]["host"]
        self.play_extraction_dir = os.path.abspath(SmApplication._read_json_config(self, "config.json")["playExtractionDir"])

        self.service_mappings = SmApplication._read_json_config(self, "service_mappings.json")
        self.features = features

        self.process_manager = process_manager

        for profile in self.profiles:
            if profile in self.services:
                print b.warning + "WARNING: The profile %s conflicts with a service of the same name, this hides the profile and makes it unusable!!!" % profile + b.endc

    def service_data(self, service_name):
        if not service_name in self.services:
            raise ServiceManagerException("Unknown service: %s" % service_name)
        return self.services[service_name]

    def services_for_profile(self, profile):
        if self.is_profile(profile):
            return self.profiles[profile]
        raise ServiceManagerException("The requested profile '%s' does not exist" % profile)

    def has_service(self, service_name):
        return service_name in self.services

    def is_profile(self, profile):
        return profile in self.profiles

    def get_merged_services_config(self):
        # the services have been merged with templates at this point
        return self.services

    def merge_template_config(self):
        for service in self.services:
            template_key = "template"
            if template_key in self.services[service]:
                template_to_use = self.services[service][template_key]
                if template_to_use in self.templates:
                    copied = copy.deepcopy(self.templates[template_to_use]) #merge_dict(self.templates[template_to_use], self.services[service])
                    original_config = copy.deepcopy(self.services[service])
                    merge_dict(copied, original_config)
                    str_version = json.dumps(copied)
                    str_replaced = str_version.replace("${SERVICE-ID}", service)
                    new_config = json.loads(str_replaced)
                    self.services[service] = new_config #hehe, take that recursion! (O)1

    def describe(self):
        print "Services:"

        for service_name in collections.OrderedDict(sorted(self.services.items())):
            print "\t" + service_name.ljust(12) + " =>\t" + self.services[service_name]["name"]

        print "Profiles:"

        for profile_name in collections.OrderedDict(sorted(self.profiles.items())):
            print "\t" + profile_name.ljust(12) + " =>\t" + ", ".join(self.profiles[profile_name])

    def _read_json_config(self, filename):
        config_file = os.path.join(self.configuration_dir, filename)

        if not os.path.isfile(config_file):
            SmApplication.exit_with_error("Cannot find configuration file: %s" % config_file)

        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception as e:
            SmApplication.exit_with_error("Unable to load configuration file '%s' due to exception: %s" % (config_file, str(e)))

    def _get_configuration_dir(self, configuration_dir_parameter):

        if configuration_dir_parameter:
            configuration_dir = configuration_dir_parameter
        else:
            configuration_dir = os.path.join(self.workspace, "service-manager-config")

        configuration_dir = os.path.abspath(configuration_dir)

        if not configuration_dir.endswith(os.sep):
            configuration_dir += os.sep

        if not os.path.isdir(configuration_dir):
            SmApplication.exit_with_error("Cannot find configuration directory: %s" % configuration_dir)

        return configuration_dir

    @staticmethod
    def _required_environment_directory(environment_variable, description_for_error):

        directory = os.environ.get(environment_variable, None)

        if not directory:
            SmApplication.exit_with_error("'%s' environment variable is required. You can add this to your ~/.bash_profile by adding the line %s=[%s]" %
                                          (environment_variable, environment_variable, description_for_error))

        directory = os.path.abspath(directory)

        if not os.path.isdir(directory):
            SmApplication.exit_with_error("'%s' environment variable points to non-existent directory: %s" % (environment_variable, directory))

        return directory

    @staticmethod
    def exit_with_error(message):
        print "Error: " + message
        sys.exit(1)


class SmContext():

    # Invocation context object - representing a call to sm.py, or a request received by SmServer

    MAX_TIME_TO_DIE_SECONDS = 3

    def __init__(self, application, test_id, offline=False, show_progress=True, request_specific_features=None, verbose=False):
        self.application = application
        self.test_id = test_id
        self.instance_id = if_not(self.test_id, "LOCAL")
        self.database_name_prefix = test_id
        self.offline = offline
        self.show_progress = show_progress
        self.verbose = verbose
        self.is_test = test_id is not None
        self.features = unify_lists(request_specific_features, self.application.features)
        self.credentials = CredentialsResolver(self)
        self.process_manager = application.process_manager
        self.assets_versions = []

    def config_value(self, key, default=None):
        if key in self.application.config:
            return self.application.config[key]
        else:
            return default

    def exception(self, message):
        self.log(message)
        return ServiceManagerException(message)

    def log(self, message, verbose_only=False):
        if not verbose_only or (verbose_only and self.verbose):
            if self.test_id:
                print "[%s] %s" % (self.test_id, message)
            else:
                print message

    def services(self):
        return (self.get_service(service_name) for service_name in self.application.services)

    def get_service(self, service_name):
        service_type = self.service_type(service_name)

        if service_type == "external":
            return SmExternalService(self, service_name)
        elif service_type == "dropwizard":
            return SmDropwizardService(self, service_name)
        elif service_type == "play":
            return SmPlayService(self, service_name)
        elif service_type == "assets":
            return SmPythonService(self, service_name)
        else:
            raise self.exception("Unknown service type '%s' for service '%s' - please check services.json" % (service_type, service_name))

    def drop_database_for_service(self, service_name):
        self._drop_database(self.database_name_prefix + "-" + service_name)

    def drop_database_for_test(self):
        self._drop_database(self.database_name_prefix)

    def _drop_database(self, database_name):
        c = MongoClient()
        try:
            if database_name in c.database_names():
                self.log("Dropping database: %s" % database_name)
                c.drop_database(database_name)
        finally:
            c.close()

    def service_data(self, service_name):
        return self.application.service_data(service_name)

    def get_microservice_target_path(self, service_name):
        data = self.service_data(service_name)
        return self.application.workspace + data["location"] + "/target/"

    def _create_extension(self, service_name, run_from):
        if self.service_type(service_name) == "play" or self.service_type(service_name) == "assets":
            ext = self.service_data(service_name)["binary"].get('ext', 'tgz')
            return "." + ext
        else:
            return "-%s-shaded.jar" % run_from

    def get_jar_filename(self, service_name, run_from):
        data = self.service_data(service_name)
        binary = data["binary"]
        artifact = binary["artifact"]
        extension = self._create_extension(service_name, run_from)
        return artifact + extension

    def assets_versions_to_start(self, version):
        self.assets_versions = self.assets_versions + version

    def kill(self, service_name=None, wait=False):
        if service_name:
            self._kill_service(service_name, wait)
        elif self.test_id:
            self._kill_test()
        else:
            self.kill_everything()

    def _kill_service(self, service_name, wait=False):
        service = self.get_service(service_name)
        self.log("Stopping '%s'" % service_name)
        service.stop(wait)

    def _kill_test(self):
        services_stopped = kill_by_test_id(self, False)
        seconds_remaining = SmContext.MAX_TIME_TO_DIE_SECONDS
        while seconds_remaining > 0 and test_has_running_processes(self):
            time.sleep(1)
            seconds_remaining -= 1
        services_stopped |= kill_by_test_id(self, True)
        self._clean_up_services(services_stopped)

    def kill_everything(self, wait=False):
        for service_name in self.application.services:
            self._kill_service(service_name, wait)

    def _clean_up_services(self, services):
        for service_name in services:
            self.get_service(service_name).clean_up()

    def has_service(self, service_name):
        return self.application.has_service(service_name)

    def service_type(self, service_name):
        service_type = self.service_data(service_name)["type"]
        if service_type not in ["dropwizard", "play", "external", "assets"]:
            raise self.exception("Unknown service type '%s' in services.json for service '%s'" % (service_type, service_name))
        return service_type

    def get_ports_used(self):
        ports_used = {}
        for service_name in self.application.services:
            service = self.application.services[service_name]
            if "defaultPort" in service:
                ports_used[service["defaultPort"]] = service_name
                if "defaultAdminPort" in service:
                    ports_used[service["defaultAdminPort"]] = service_name
        return ports_used

    def is_profile(self, profile):
        return self.application.is_profile(profile)

    def get_run_from_service_override_value_or_use_default(self, service, original_runfrom):
        if "always_run_from" in service.service_data:
            if validate_run_from(service.service_data["always_run_from"]):
                self.log("Service '%s' has been overridden to always use '%s' version" % (service.service_name, service.service_data["always_run_from"]), True)
                return service.service_data["always_run_from"]

        if original_runfrom == "DEFAULT":
            if ("default_run_from" in service.service_data) and validate_run_from(service.service_data["default_run_from"]):
                return service.service_data["default_run_from"]
            else:
                return "SOURCE"

        return original_runfrom

    def get_service_starter(self, service_name, run_from, proxy, classifier=None, service_mapping_ports=None, port=None, admin_port=None, version=None, append_args=None):
        service = self.get_service(service_name)
        run_from = self.get_run_from_service_override_value_or_use_default(service, run_from)

        if not service_mapping_ports:
            service_mapping_ports = {}

        service_type = self.service_type(service_name)

        if (not self.is_test) and service.is_started_on_default_port():
            print service_name + " is already running on its default port, not starting a new one"
            return None

        if service_type == "external":
            starter = SmExternalServiceStarter(self, service_name, append_args)
        elif service_type == "dropwizard":
            starter = SmDropwizardServiceStarter(self, service_name, run_from, port, admin_port, classifier, service_mapping_ports, version, proxy, append_args)
        elif service_type == "play":
            starter = SmPlayServiceStarter(self, service_name, run_from, port, classifier, service_mapping_ports, version, proxy, append_args)
        elif service_type == "assets":
            proxy = None
            starter = SmPythonServiceStarter(self, service_name, run_from, port, classifier, service_mapping_ports, version, proxy, append_args)
        else:
            raise self.exception("Unknown service type '%s' for service '%s' - please check services.json" % (service_type, service_name))

        return starter

    def start_service(self, service_name, run_from, proxy, classifier=None, service_mapping_ports=None, port=None, admin_port=None, version=None, appendArgs=None):
        feature_string = pretty_print_list(" with feature$s $list enabled", self.features)
        self.log("\nStarting '%s' from %s%s... " % (service_name, run_from, feature_string))
        service_starter = self.get_service_starter(service_name, run_from, proxy, classifier, service_mapping_ports, port, admin_port, version, appendArgs)
        service_process_id = service_starter.start()

        if service_process_id:
            feature_string = pretty_print_list(" and feature$s $list enabled", self.features)
            self.log("'%s' started with PID = %d%s" % (service_name, service_process_id, feature_string), True)
        else:
            self.log("'%s' does not appear to have started" % service_name)

        return service_process_id
