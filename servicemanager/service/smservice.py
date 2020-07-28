#!/usr/bin/env python

from abc import abstractmethod


class SmServiceBase:
    def __init__(self, context, service_name, expected_service_type):
        self.context = context
        self.service_name = service_name
        self.service_data = self.context.service_data(service_name)
        self.service_type = context.service_type(service_name)

        if self.service_type != expected_service_type:
            raise context.exception(
                "Cannot construct '%s' as type '%s', services.json states its type is: '%s'"
                % (service_name, expected_service_type, self.service_type)
            )

    def log(self, message, verbose_only=False):
        self.context.log("[%s]: %s" % (self.service_name, message), verbose_only)

    def required_data(self, key):
        value = self.service_data.get(key, None)

        if not value:
            message = "Missing required '%s' configuration in services.json" % key
            self.log(message)
            raise self.context.exception(message)

        return value


class SmService(SmServiceBase):
    def __init__(self, context, service_name, expected_service_type):
        SmServiceBase.__init__(self, context, service_name, expected_service_type)

    @abstractmethod
    def is_started_on_default_port(self):
        pass

    @abstractmethod
    def request_running_service_details_on_default_port(self):
        pass

    @abstractmethod
    def status(self, all_processes):
        pass

    @abstractmethod
    def run_healthcheck(self, process):
        pass

    @abstractmethod
    def get_pattern(self):
        pass


class SmServiceStarter(SmServiceBase):
    def __init__(self, context, service_name, expected_service_type, append_args):
        SmServiceBase.__init__(self, context, service_name, expected_service_type)
        self.append_args = append_args

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def process_arguments(self):
        pass

    @abstractmethod
    def supports_append_args(self):
        return False

    @abstractmethod
    def get_start_command(self, context=None):
        return ["get_start_command() not implemented for this type of service - fork and make a pull request :)"]


class SmMicroServiceStarter(SmServiceStarter):
    def __init__(
        self,
        context,
        service_name,
        expected_service_type,
        run_from,
        port,
        classifier,
        service_mapping_ports,
        version,
        proxy,
        append_args,
    ):
        SmServiceStarter.__init__(self, context, service_name, expected_service_type, append_args)

        self.run_from = run_from
        self.version = version
        self.classifier = classifier
        self.service_mapping_ports = service_mapping_ports
        self.port = port if port else self.service_data["defaultPort"]
        self.proxy = proxy

        if "sources" not in self.service_data:
            raise context.exception(
                "Invalid services.json entry for %s service '%s', missing 'sources'"
                % (self.service_type, self.service_name)
            )

        self.sources = self.service_data["sources"]

    @abstractmethod
    def start(self, appendArgs=None):
        pass

    @abstractmethod
    def process_arguments(self):
        pass


class SmServiceStatus:

    HEALTHCHECK_NONE = "NONE"
    HEALTHCHECK_PASS = "PASS"
    HEALTHCHECK_BOOT = "BOOT"

    def __init__(
        self, service_name, ppid, pid, uptime, mem, port, test_id, run_from, features, healthcheck,
    ):
        self.service_name = service_name
        self.ppid = ppid
        self.pid = pid
        self.uptime = uptime
        self.mem = mem
        self.port = port
        self.test_id = test_id
        self.run_from = run_from
        self.features = features
        self.healthcheck = healthcheck

    @staticmethod
    def for_process(service_name, process, port, test_id, run_from, features, healthcheck):
        return SmServiceStatus(
            service_name,
            process.ppid,
            process.pid,
            process.uptime,
            process.mem,
            port,
            test_id,
            run_from,
            features,
            healthcheck,
        )
