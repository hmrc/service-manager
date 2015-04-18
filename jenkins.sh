#!/bin/bash

py.test -v --junitxml results.xml test/tests.py 
py.test -v --junitxml results.xml test/unit
