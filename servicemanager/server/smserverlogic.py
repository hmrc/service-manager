#!/usr/bin/env python

import json
import time
import requests
import sys
import traceback
import re
import types

from abc import abstractmethod
from bottle import request, response

from ..smcontext import SmContext, ServiceManagerException
from ..smport import PortProvider

RUN_ON_PORT = 8085
RUN_ON_HOST = 'localhost'
SERVICE_START_TIMEOUT_SECONDS = 90
MAX_TEST_ID_LENGTH = 40

deprecated_release_params = {"SNAPSHOT_JAR": "SNAPSHOT", "RELEASE_JAR": "RELEASE"}


class BadRequestException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class SmResponse:

    def __init__(self):
        pass  # Do nothing

    @staticmethod
    def bad_request(message):
        print "Bad Request: " + message
        response.status = 400
        return json.dumps({"statusCode": 400, "errorMessage": message})

    @staticmethod
    def error_500(message):
        response.status = 500
        return json.dumps({"statusCode": 500, "errorMessage": message})


class SmRequest:

    def __init__(self, server, json_body, offlineMode, show_progress, verbose):
        self.server = server
        self.json_body = json_body

        try:
            test_id = self.json_body["testId"]
        except Exception:
            raise BadRequestException("Missing testId parameter")

        SmRequest._validate_test_id(test_id)

        request_specific_features = SmRequest._extract_and_validate_request_specific_features(self.json_body)

        self.test_id = test_id
        self.context = SmContext(server.application, self.test_id, show_progress=show_progress, request_specific_features=request_specific_features, offline=offlineMode, verbose=verbose)

    @abstractmethod
    def process_request(self):
        pass

    @staticmethod
    def _extract_and_validate_request_specific_features(json_body):

        if not "features" in json_body:
            return None

        request_specific_features = json_body["features"]

        if not request_specific_features:
            return None

        if not isinstance(request_specific_features, list):
            raise BadRequestException("'features' must be a list of strings")

        for feature in request_specific_features:
            if not isinstance(feature, basestring):
                raise BadRequestException("'features' must be a list of strings")

        return request_specific_features

    def _bad_request_exception(self, message):
        return BadRequestException("[%s] %s" % (self.test_id, message))

    def _log(self, message):
        self.context.log(message)

    @staticmethod
    def _validate_test_id(test_id):
        regex = re.compile("^[a-zA-Z0-9\-_]+$")

        if not regex.match(test_id):
            raise BadRequestException("Invalid parameter 'testId' with value '%s', valid characters are 'a-z', 'A-Z', '0-9', '-' and '_'" % test_id)

        if test_id.upper() == "LOCAL":
            raise BadRequestException("'%s' is not a valid value for testId" % test_id)

        if len(test_id) > MAX_TEST_ID_LENGTH:
            raise BadRequestException("Test id '%s' is too long (%d characters) (maximum is %d characters)" % (test_id, len(test_id), MAX_TEST_ID_LENGTH))

    def _get_or_throw_bad_request(self, obj, key, message):
        if key not in obj:
            raise self._bad_request_exception(message)

        value = obj[key]

        if not value:
            raise self._bad_request_exception(message)

        return value

    def _stop_services(self, drop_databases):

        self._log("Stopping services (drop databases = %s)" % drop_databases)

        errors = self.context.kill()

        if drop_databases:
            for service_name in self.server.service_names_for_test(self.test_id):
                if self.context.service_data(service_name).get("hasMongo", False):
                    self.context.drop_database_for_service(service_name)

            self.context.drop_database_for_test()

        self.server.test_stopped(self.test_id)

        return errors


class SmStartRequest(SmRequest):

    def __init__(self, server, json_request_body, do_not_run_from_source, offlineMode, show_progress, verbose):
        self.do_not_run_from_source = do_not_run_from_source
        self.json_body = json_request_body
        SmRequest.__init__(self, server, self.json_body, offlineMode, show_progress, verbose)

    def process_request(self):
        # START REQUEST PAYLOAD:
        #  {
        #   "testId": "blah",
        #   "features": ["feature1", "feature2", ...],
        #   "services": [
        #       {"serviceName" : "auth", "runFrom" : "SNAPSHOT"},
        #       {"serviceName" : "matching", "runFrom" : "RELEASE", "version" : "3.0.1"},
        #       {"serviceName" : "portal", "runFrom" : "SOURCE"},
        #       {"serviceName" : "nps",  "runFrom" : "SOURCE"},
        #       ...
        #   ]
        # }

        self._log("Processing service start request")

        if self.server.is_running(self.test_id):
            raise self._bad_request_exception("Test '%s' is already running" % self.test_id)

        self.server.starting_test(self.test_id)

        services_to_start = self._get_or_throw_bad_request(self.json_body, "services", "'services' missing from request")

        self._log("Service(s) to start: " + str(services_to_start))

        (orchestration_services, service_mapping_ports) = self._validate_start_request_and_assign_ports(services_to_start, self.do_not_run_from_source)

        try:
            self._start_services_for_test(orchestration_services, service_mapping_ports)

            sm_response = []

            for service_mapping_name in service_mapping_ports:
                sm_response += [{"serviceName": service_mapping_name, "port": service_mapping_ports[service_mapping_name]}]

            self._log("All services started! To kill the running processes for this test, POST {\"testId\":\"%s\"} to http://%s:%s/stop" % (self.test_id, RUN_ON_HOST, RUN_ON_PORT))

            return json.dumps(sm_response)

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return self._stop_services_and_return_500("Unexpected exception: " + e.message)

    # {"AUTH": {"port": 43124, "runFrom":"JAR", "serviceMapping" : "auth"}}
    def _start_services(self, orchestration_services, service_mapping_ports, proxy):

        for service_name in orchestration_services:

            port = orchestration_services[service_name]["port"]
            admin_port = orchestration_services[service_name]["adminPort"]
            run_from = orchestration_services[service_name]["runFrom"]
            classifier = orchestration_services[service_name]["classifier"]
            version = orchestration_services[service_name]["version"]
            append_args = orchestration_services[service_name]["appendArgs"] # Allows for dynamic config overriding

            # Allow for deprecated run_from values
            if run_from in deprecated_release_params:
                run_from = deprecated_release_params[run_from]

            self.context.start_service(service_name, run_from, proxy, classifier, service_mapping_ports, port, admin_port, version, append_args)

    def _await_service_startup(self, service_name, port, admin_port):
        seconds_remaining = SERVICE_START_TIMEOUT_SECONDS

        servicedata = self.context.service_data(service_name)
        if "healthcheck" in servicedata:
            healthcheck_url = servicedata["healthcheck"]["url"].replace("${port}", str(admin_port))
            healthcheck_response_regex = self.context.service_data(service_name)["healthcheck"]["response"]

            while seconds_remaining > 0:
                if (seconds_remaining < 10 or seconds_remaining % 5 == 0) and seconds_remaining != 1:
                    self._log("Waiting for %s to start on port %d, %d seconds before timeout" % (service_name, port, seconds_remaining))
                elif seconds_remaining == 1:
                    self._log("Waiting for %s to start on port %d, 1 second before timeout" % (service_name, port))

                try:
                    ping_response = requests.get(healthcheck_url)
                    response_text = ping_response.text
                    healthcheck = re.search(healthcheck_response_regex, response_text)
                except requests.RequestException:
                    healthcheck = False

                if healthcheck or (seconds_remaining == 0):
                    self._log("Service %s health check SUCCESSFUL" % service_name)
                    break
                else:
                    seconds_remaining -= 1
                    time.sleep(1)

                if seconds_remaining <= 0:
                    raise self.context.exception("Service %s - healthcheck did not pass within allocated time (%d seconds)" % (service_name, SERVICE_START_TIMEOUT_SECONDS))
        else:
            self._log("There is no health check for '%s'. This is not really advisable we can only assume it has started correctly" % service_name)

    def _start_services_for_test(self, orchestration_services, service_mapping_ports):

        self._start_services(orchestration_services, service_mapping_ports, None)

        for service_name in orchestration_services:

            self.server.starting_service_for_test(self.test_id, service_name)

            port = orchestration_services[service_name]["port"]
            admin_port = orchestration_services[service_name]["adminPort"]

            self._await_service_startup(service_name, port, admin_port)

    def _stop_services_and_return_500(self, message):
        self._log(message)
        errors = self._stop_services(drop_databases=True)

        if errors:
            self._log("Errors during shutdown: %s" % str(errors))

        return SmResponse.error_500(message)

    def _service_mapping_for(self, service_start_request):

        service_mapping_name = self._get_or_throw_bad_request(service_start_request, "serviceName", "Missing 'serviceName' parameter in instruction to start services")

        mapping = self._get_or_throw_bad_request(self.context.application.service_mappings, service_mapping_name, "Unknown service name '%s'" % service_mapping_name)

        need_classifier = isinstance(mapping, dict)
        have_classifier = "classifier" in service_start_request and service_start_request["classifier"]

        version = None
        if "version" in service_start_request and service_start_request["version"]:
            version = service_start_request["version"]

        append_args = service_start_request.get("appendArgs", [])

        if need_classifier:

            valid_classifiers = "[" + (",".join(str(x) for x in mapping.keys())) + "]"

            if not have_classifier:
                raise self._bad_request_exception("Service '%s' requires a classifier (one of: %s)" % (service_mapping_name, valid_classifiers))

            classifier = service_start_request["classifier"]

            if classifier not in mapping:
                raise self._bad_request_exception("Unknown classifier '%s' for service '%s' (expected one of: %s)" % (classifier, service_mapping_name, valid_classifiers))

            service_name = mapping[classifier]

        else:

            if have_classifier:
                raise self._bad_request_exception("Service '%s' does not take classifiers (found: '%s')" % (service_mapping_name, service_start_request["classifier"]))

            service_name = mapping
            classifier = None

        return service_mapping_name, service_name, classifier, version, append_args

    def _validate_start_request_and_assign_ports(self, services_to_start, dontrunfromsource):

        orchestration_services = {}
        service_mapping_ports = {}

        for service_start_request in services_to_start:

            service_mapping_name, service_name, classifier, version, append_args = self._service_mapping_for(service_start_request)

            if append_args and not isinstance(append_args, types.ListType):
                raise self._bad_request_exception("ERROR: I was passed a non list for append args of '" + str(append_args) + "' I dont know what to do with this")

            if service_mapping_name in service_mapping_ports:
                raise self._bad_request_exception("Duplicate entry for service '%s' in start request" % service_mapping_name)

            run_from = self._get_or_throw_bad_request(service_start_request, "runFrom", "Missing 'runFrom' parameter in instruction to start '%s'" % service_mapping_name)

            if run_from not in ["SOURCE", "SNAPSHOT", "RELEASE"] + deprecated_release_params.keys():
                raise self._bad_request_exception("runFrom parameter has invalid value '%s' (should be 'SOURCE', 'SNAPSHOT' or 'RELEASE')" % run_from)

            if dontrunfromsource:
                if run_from == "SOURCE":
                    raise self._bad_request_exception("runFrom parameter has value '%s', however --nosource was specified when smserver started" % run_from)

            if append_args and not self.context.get_service_starter(service_name, run_from, None).supports_append_args():
                raise BadRequestException("The service type for '" + service_name + "' does not support append args")

            if service_name in orchestration_services:
                existing_entry = orchestration_services[service_name]
                service_mapping_ports[service_mapping_name] = existing_entry["port"]

                if run_from != existing_entry["runFrom"]:
                    raise self._bad_request_exception("Conflicting runFrom values (%s and %s) for underlying service '%s'" % (run_from, existing_entry["runFrom"], service_name))

                if classifier and existing_entry["classifier"] and classifier != existing_entry["classifier"]:
                    raise self._bad_request_exception("Conflicting classifier values (%s and %s) for underlying service '%s'" % (classifier, existing_entry["classifier"], service_name))

            else:
                port = self.server.next_available_port()
                admin_port = self.server.next_available_port() if self.context.service_type(service_name) == "dropwizard" else port

                service_mapping_ports[service_mapping_name] = port

                orchestration_services[service_name] = {
                    "port": port,
                    "adminPort": admin_port,
                    "runFrom": run_from,
                    "classifier": classifier,
                    "version": version,
                    "appendArgs": append_args
                }

        return orchestration_services, service_mapping_ports


class SmStopRequest(SmRequest):

    def __init__(self, server, json_request_body, offlineMode, show_progress, verbose):
        SmRequest.__init__(self, server, json_request_body, offlineMode, show_progress, verbose)

    def process_request(self):

        if not self.server.is_running(self.test_id):
            raise BadRequestException("Invalid test id (or already stopped): %s" % self.test_id)

        self._log("Stopping test")

        drop_databases = self.json_body.get("dropDatabases", True)

        if type(drop_databases) is not bool:
            raise self._bad_request_exception("dropDatabases parameter must be boolean (value was: %s)" % drop_databases)

        errors = self._stop_services(drop_databases)

        if errors:
            self._log("Completed stopping services - errors occurred: %s" % str(errors))
            response.status = 500
            return json.dumps({"statusCode": 500, "errorMessage": errors})
        else:
            self._log("Successfully stopped services")
            response.status = 204


class SmShutdownRequest():

    def __init__(self, server):
        self.server = server

    def process_request(self):
        print "shutting down..."
        for test_id in self.server.running_tests:
            context = SmContext(self.server.application, test_id)
            context.log("Killing everything for testId %s..." % test_id)
            context.kill()
            for service_name in self.server.service_names_for_test(test_id):
                if context.service_data(service_name).get("hasMongo", False):
                    context.drop_database_for_service(service_name)

            context.drop_database_for_test()
            context.log("Successfully stopped all services for testId %s..." % test_id)

        print "finished shutting down..."


class SmServer:

    def __init__(self, application):

        self.application = application
        self.port_provider = PortProvider()

        # Map of test_id to list of service names
        self.running_tests = {}

    def next_available_port(self):
        return self.port_provider.next_available_port()

    def service_names_for_test(self, test_id):
        if self.is_running(test_id):
            return self.running_tests[test_id]
        else:
            return []

    def is_running(self, test_id):
        return test_id in self.running_tests

    def starting_test(self, test_id):
        if self.is_running(test_id):
            raise ServiceManagerException("Test '%s' is already running" % test_id)
        self.running_tests[test_id] = []

    def starting_service_for_test(self, test_id, service_name):
        if not self.is_running(test_id):
            raise ServiceManagerException("Test '%s' is not running" % test_id)
        self.running_tests[test_id] += [service_name]

    def test_stopped(self, test_id):
        del self.running_tests[test_id]


class SmVersionRequest:

    def __init__(self, server):
        self.application = server.application

    def process_request(self):
        service = request.query['service']
        if not service in self.application.service_mappings:
            raise BadRequestException("Service '%s' cannot be found in 'service_mappings.json', please update this file" % service)
        service_alias = self.application.service_mappings[service]
        if not service_alias in self.application.services:
            raise BadRequestException("Service '%s' cannot be found in 'services.json', please update this file" % service_alias)
        if not "versionEnv" in self.application.services[service_alias]:
            raise BadRequestException("'versionEnv' cannot be found for service '%s', please update 'services.json'" % service_alias)
        return {"variable": self.application.services[service_alias]["versionEnv"]}
