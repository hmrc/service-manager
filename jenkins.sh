#!/bin/bash
export JAVA_HOME=${JAVA_HOME:=$(/usr/libexec/java_home)}
export WORKSPACE=${WORKSPACE:='.'}
export NEXUS_PASS=${NEXUS_PASS:='fake'}
export NEXUS_USER=${NEXUS_USER:='fake'}
py.test -v --junitxml results.xml test/tests.py
py.test -v --junitxml results.xml test/unit
