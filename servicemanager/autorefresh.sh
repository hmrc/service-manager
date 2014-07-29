#! /bin/sh

clear

while true
do

    if [ "$1" = "--test" ] 
    then
        sm --status --config $WORKSPACE/service-manager-config > /tmp/smstatus.txt 2>&1
    else
        sm --status > /tmp/smstatus.txt 2>&1
    fi

    clear
    cat /tmp/smstatus.txt
    sleep 2
done
