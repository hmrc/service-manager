#!/usr/bin/env bash
# this script is here to allow the testting of additional parameters being passed to a script.
# the parameters are multiplied together. If they don't exist, they are defaulted to zeo
sleep $(($1 * ${2:-1}))