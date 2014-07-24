#!/usr/bin/env python
import sys
import os
import json

from servicemanager import subprocess


try:
    args = json.loads(sys.argv[1])
    print u"Executing: %s" % " ".join(args)
    print u"SBT_EXTRA_PARAMS: %s" % os.environ["SBT_EXTRA_PARAMS"]
    out = subprocess.check_output(args, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    print u"Output: %s" % out

except subprocess.CalledProcessError as e:
    print "\n*****************************************"
    print "sbt execution FAILED: exit code = %s" % e.returncode
    print "Directory: %s" % os.getcwd()
    print "-----------------------------------------"
    print e.output
    print "*****************************************"
    sys.exit(e.returncode)