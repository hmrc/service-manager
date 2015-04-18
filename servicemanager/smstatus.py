#!/usr/bin/env python

from servicemanager.thirdparty.prettytable import PrettyTable
from servicemanager.service.smservice import SmServiceStatus
from servicemanager.smcontext import ServiceManagerException
from servicemanager.actions.colours import BColors

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


def dostatus(context, show_down_services):
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


    all_processes = context.process_manager.all_processes()
    for service in context.services():
        responses = service.status(all_processes)
        if responses:
            for response in responses:
                up_processes_table.add_row(_service_status_to_row(response))
        elif show_down_services:
            down_processes_table.add_row([service.service_name, b.bold + b.fail + "DOWN" + b.endc])

    result = ["Running:", str(up_processes_table)]
    if show_down_services:
        result.append("Down:")
        result.append(str(down_processes_table))
    return result