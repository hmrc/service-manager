#!/bin/bash
export JAVA_HOME=${JAVA_HOME:=$(/usr/libexec/java_home)}
export WORKSPACE=${WORKSPACE:='.'}
export NEXUS_PASS=${NEXUS_PASS:='sbt_creds'}
export NEXUS_USER=${NEXUS_USER:='sbt'}
py.test -v --junitxml results.xml test/
