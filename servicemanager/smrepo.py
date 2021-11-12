#!/usr/bin/env python
import os

from .actions.colours import BColors
import subprocess


b = BColors()


def pull_rebase_repo(context, name, project_info):
    if "sources" in project_info and "repo" in project_info["sources"]:
        print("pulling '" + name + "' from repo '" + project_info["sources"]["repo"] + "'")
        path = context.application.workspace + project_info["location"]
        if not os.path.exists(path):
            print(
                b.fail
                + "Nothing was pulled, it appears you have not cloned this repo yet: '"
                + name
                + "'"
                + b.endc
                + "\n"
            )
        else:
            os.chdir(path)
            command = "git pull --rebase"
            print("running: '" + command + "' from: '" + os.getcwd() + "'")
            ps_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            stdout, _ = ps_command.communicate()
            if ps_command.returncode != 0:
                print(b.fail + "Nothing was pulled, see output for: '" + name + "'" + b.endc)
            else:
                print(b.okgreen + "Pulled: '" + name + "'" + b.endc)
            print(stdout)


def clone_repo_if_required_raw(service_name, repo, path, context):
    path_exists = True
    if not os.path.exists(path):
        path_exists = False
        context.log("Source code for %s is missing, cloning..." % service_name)
        os.chdir(context.application.workspace)
        command = "git clone --depth 1 %s" % repo
        ps_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        ps_command.communicate()
        if ps_command.returncode != 0:
            print(b.fail + "ERROR: Unable to clone repo for '" + service_name + "'" + b.endc)
        if os.path.exists(path):
            path_exists = True
            print(service_name + " - cloned")
        else:
            # TODO Should this just throw an exception?
            context.log("Could not go to dir: " + path + " do you have the project: " + service_name + " checked out?")
    elif os.path.exists(path + "/.git"):
        # TODO: make non os dependent
        print(service_name + " - source exists")
    else:
        print(
            b.warning
            + "WARNING: Nothing was cloned for '"
            + service_name
            + "' folder '"
            + path
            + "' already exists and it does not contain a repo"
            + b.endc
        )

    return path_exists


def clone_repo_if_requred(service):

    context = service.context
    service_data = service.service_data
    sources_data = service.sources
    path = context.application.workspace + service_data["location"]

    return clone_repo_if_required_raw(service.service_name, sources_data["repo"], path, context)
