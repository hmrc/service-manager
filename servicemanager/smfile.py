import os
import shutil


def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)


def remove_folder_if_exists(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def makedirs_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def force_chdir(path):
    makedirs_if_not_exists(path)
    os.chdir(path)

