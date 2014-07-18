#! /bin/sh

clear

while true
do

    if [ "$1" = "--test" ] 
    then
        python sm.py --status --config $WORKSPACE/application-manager/src/universal/test/conf/ > /tmp/smstatus.txt 2>&1
    else
        python sm.py --status > /tmp/smstatus.txt 2>&1
    fi

    clear
    cat /tmp/smstatus.txt
    sleep 2
done
