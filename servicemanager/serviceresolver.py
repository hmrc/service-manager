import re


class ServiceResolver:
    def __init__(self, application):
        self.application = application

    def resolve_services(self, service_name):
        return self.resolve_services_from_array([service_name])

    def resolve_services_from_array(self, services):
        services_to_start = []
        services_to_not_start = []

        for service_name in services:
            if service_name.startswith("-"):
                services_to_not_start += self.resolve_services(service_name[1:])
            elif "*" in service_name:
                services_to_start += self._all_matching(service_name)
            elif self.application.has_service(service_name):
                services_to_start += [service_name]
            elif self.application.is_profile(service_name):
                services_to_start += self._get_all_in_profile(service_name)
            else:
                print("The requested service %s does not exist" % service_name)
        for not_start in services_to_not_start:
            if not_start in services_to_start:
                services_to_start.remove(not_start)
        return services_to_start

    def _find_assets_service_name(self, service_name):
        assets_service_name = ""
        for service_name in self.application.services:
            if self.application.services[service_name]["type"] == "assets":
                assets_service_name = service_name
        return assets_service_name

    def _get_all_in_profile(self, profile_name):
        services = []
        services_to_not_start = []

        assets_service_name = self._find_assets_service_name(profile_name)

        for service_name in self.application.services_for_profile(profile_name):
            if service_name.startswith("-"):
                services_to_not_start += self._all_matching(service_name[1:])
            elif "*" in service_name:
                services += self._all_matching(service_name)
            elif self.application.has_service(service_name):
                services.append(service_name)
            else:
                print("The requested service %s does not exist" % service_name)
        for not_start in services_to_not_start:
            if not_start in services:
                services.remove(not_start)
        if assets_service_name in services:
            services.remove(assets_service_name)
            services.append(assets_service_name)
        return services

    def _all_matching(self, wildcard):
        services = []
        for service_name in self.application.services:
            if ServiceResolver._matches(service_name, wildcard):
                services.append(service_name)
        return services

    @staticmethod
    def _matches(service_name, wildcard):
        regex = re.compile(wildcard.replace("*", ".*"))
        return re.match(regex, service_name)
