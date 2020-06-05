#!/bin/bash

# Some of the test applications in this project need Java 8 in order to work
# properly. However, TravisCI's Ubuntu >=16.04 ships with Java 11, and Java
# can't be set with `jdk` when python is selected as language.
# An alternative to this is to set 'dist:trusty', and pin Ubuntu to 14.04
# for Travis builds.

# show current JAVA_HOME and java version
echo "Existing JAVA_HOME: $JAVA_HOME"
echo "Existing java -version:"
java -version

# install Java 8
sudo add-apt-repository -y ppa:openjdk-r/ppa
sudo apt-get -qq update
sudo apt-get install -y openjdk-8-jdk --no-install-recommends
sudo update-java-alternatives -s java-1.8.0-openjdk-amd64

# change JAVA_HOME to Java 8
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
echo "Current java -version:"
java -version
