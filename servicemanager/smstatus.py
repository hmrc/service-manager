#!/usr/bin/env python

from servicemanager.thirdparty.prettytable import PrettyTable
from servicemanager.service.smservice import SmServiceStatus
from servicemanager.smcontext import ServiceManagerException
from servicemanager.actions.colours import BColors

import os

def _format_healthcheck_status(healthcheck):
    b = BColors()
    if healthcheck == SmServiceStatus.HEALTHCHECK_PASS:
        return b.bold + b.okgreen + "PASS" + b.endc
    elif healthcheck == SmServiceStatus.HEALTHCHECK_BOOT:
        return b.bold + b.warning + "BOOT" + b.endc
    elif healthcheck == SmServiceStatus.HEALTHCHECK_NONE:
        return b.okblue + "NONE" + b.endc
    else:
        raise ServiceManagerException("Unknown healthcheck status: %s" % healthcheck)


def _service_status_to_row(status):
    return [
        status.service_name,
        status.ppid,
        status.pid,
        status.uptime,
        status.mem,
        status.port,
        status.test_id,
        status.run_from,
        status.features,
        _format_healthcheck_status(status.healthcheck)
    ]


def dostatus(context, services, show_down_services, clear_before_print=False):
    b = BColors()
    up_processes_table = PrettyTable()
    up_processes_table.field_names = ["name", "ppid", "pid", "uptime", "mem", "port", "test id", "run from", "features", "healthcheck"]
    up_processes_table.align = "r"
    up_processes_table.align["name"] = "l"
    up_processes_table.sortby = "name"
    up_processes_table.align["test id"] = "l"
    up_processes_table.align["run from"] = "l"
    up_processes_table.align["features"] = "l"

    down_processes_table = PrettyTable()
    down_processes_table.field_names = ["name", "healthcheck"]
    down_processes_table.align = "r"
    down_processes_table.align["name"] = "l"
    down_processes_table.sortby = "name"

    if len(services) == 0:
        services = context.application.services

    for service_name in services:
        responses = context.get_service(service_name).status()
        if responses:
            for response in responses:
                up_processes_table.add_row(_service_status_to_row(response))
        elif show_down_services:
            down_processes_table.add_row([service_name, b.bold + b.fail + "DOWN" + b.endc])

    # Perhaps there is a better way of doing this by clearing the buffer
    # but this will do the trick for now
    if clear_before_print:
        os.system("clear") # Linux only I think, but thats all we currently support, so... I guess that's ok

    print "Running:"
    print up_processes_table
    if show_down_services:
        print "Down:"
        print down_processes_table
