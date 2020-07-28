#!/usr/bin/env python
import os
import time
import calendar
import glob

import subprocess
from servicemanager.smcontext import ServiceManagerException
from servicemanager.smprocess import SmProcess
from servicemanager.service.smplayservice import SmPlayService


def start_one(context, service_name, source, fatjar, release, proxy, port=None, appendArgs=None):
    if release:
        run_from = "RELEASE"
    elif fatjar:
        run_from = "SNAPSHOT"
    elif source:
        run_from = "SOURCE"
    else:
        run_from = "DEFAULT"

    version = release
    if version == "LATEST":
        version = None

    existing_service_status = context.get_service(service_name).status()

    if len(existing_service_status) > 0:
        print(
            (
                "There is already: '%s' instance(s) of the service: '%s' running"
                % (str(len(existing_service_status)), service_name)
            )
        )
        return False

    if context.start_service(service_name, run_from, proxy, port=port, version=version, appendArgs=appendArgs):
        if context.get_service(service_name).is_started_on_default_port():
            print(("Started: %s" % service_name))
            return True

    return False


def get_start_cmd(context, service_name, source, fatjar, release, proxy, port=None, append_args=None):
    if release:
        run_from = "RELEASE"
    elif fatjar:
        run_from = "SNAPSHOT"
    elif source:
        run_from = "SOURCE"
    else:
        run_from = "DEFAULT"

    version = release
    if version == "LATEST":
        version = None

    starter = context.get_service_starter(
        service_name, run_from, proxy, port=port, version=version, append_args=append_args,
    )
    return starter.get_start_command(run_from)


def stop_profile(context, profile):
    for service_name in context.application.services_for_profile(profile):
        context.kill(service_name)


def _now():
    return int(calendar.timegm(time.gmtime()))


def _wait_for_services(context, service_names, seconds_to_wait):

    waiting_for_services = []

    for service_name in service_names:
        if "healthcheck" in context.service_data(service_name):
            waiting_for_services += [context.get_service(service_name)]

    if not seconds_to_wait:
        seconds_to_wait = 0

    end_time = _now() + seconds_to_wait

    while waiting_for_services and _now() < end_time:

        services_to_check = list(waiting_for_services)

        for service in services_to_check:

            if _now() >= end_time:
                break

            processes = SmProcess.processes_matching(service.pattern)
            if all(map(service.run_healthcheck, processes)):
                print(("Service '%s' has started successfully" % service.service_name))
                waiting_for_services.remove(service)
            else:
                seconds_remaining = end_time - _now()
                if seconds_remaining % 5 == 0 or seconds_remaining < 10:
                    print(
                        (
                            "Waiting for %s to start, %s second%s before timeout"
                            % (service.service_name, seconds_remaining, "s" if seconds_to_wait != 1 else "",)
                        )
                    )

        if waiting_for_services:
            time.sleep(1)

    if waiting_for_services:
        services_timed_out = []
        for service in waiting_for_services:
            services_timed_out += [service.service_name]
        raise ServiceManagerException("Timed out starting service(s): %s" % ", ".join(services_timed_out))


def clean_logs(context, service_name):
    data = context.service_data(service_name)
    if "location" in data:
        sources_logs = context.application.workspace + data["location"] + "/logs/*.log*"
        fatjar_logs = context.application.workspace + data["location"] + "/target/logs/*.log*"

        num_files = _remove_files_wildcard(sources_logs)
        num_files += _remove_files_wildcard(fatjar_logs)
        print(("Removed %d log files in %s" % (num_files, service_name)))


def _remove_files_wildcard(files):
    r = glob.glob(files)
    for i in r:
        os.remove(i)
    return len(r)


def overridden_port(services, port):
    if len(services) == 1 and port is not None:
        return port
    else:
        return None


def _get_running_process_args(context, service_name):

    service = context.get_service(service_name)

    pattern = service.get_pattern()

    if service.is_started_on_default_port():
        command = "ps -eo args | egrep '%s' | egrep -v 'egrep %s' | awk '{{print  } }'" % (pattern, pattern)
        ps_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        ps_output = ps_command.stdout.read()

        if ps_output:
            return ps_output.split("\n")[:-1][0]

    return ""


def _get_git_rev(context, service_name):
    details = context.get_service(service_name).request_running_service_details_on_default_port()

    if details:
        return details.get("Git-Head-Rev", "")

    return ""


def display_info(context, service_name):
    arguments = _get_running_process_args(context, service_name)
    git_revision = _get_git_rev(context, service_name)
    print()
    print(("| %s" % service_name))
    print(("| %s" % arguments))
    print(("| %s" % git_revision))
    comments = ""
    if git_revision == "":
        comments += "(No Details) "
    if arguments == "":
        comments += "(Not Running) "
    print(("| %s" % comments))


def start_and_wait(
    service_resolver, context, start, source, fatjar, release, proxy, port, seconds_to_wait, append_args,
):

    all_services = service_resolver.resolve_services_from_array(start)
    for service_name in all_services:
        if context.has_service(service_name):
            append_args_for_this_service = None
            if append_args is not None:
                append_args_for_this_service = append_args.get(service_name, None)
            start_one(
                context,
                service_name,
                source,
                fatjar,
                release,
                proxy,
                overridden_port(start, port),
                append_args_for_this_service,
            )
        else:
            print(("The requested service %s does not exist" % service_name))

    if seconds_to_wait:
        _wait_for_services(context, all_services, seconds_to_wait)

    print("\nAll services passed healthcheck")


def get_log_file(context, service_name):
    def mtime(path):
        try:
            return os.path.getmtime(path)
        except os.error:
            return 0

    data = context.service_data(service_name)
    if "location" in data:
        logs = [
            context.application.workspace + data["location"] + "/logs/stdout.txt",
            context.application.workspace + data["location"] + "/target/logs/stdout.txt",
            SmPlayService.unzipped_dir_path(context, data["location"]) + "/logs/stdout.txt",
        ]
        if not any([os.path.exists(log) for log in logs]):
            raise ServiceManagerException("Cannot find log files for %s" % service_name)
        else:
            return sorted(logs, key=mtime, reverse=True)[0]
    else:
        raise ServiceManagerException("Cannot find a location for %s" % service_name)
