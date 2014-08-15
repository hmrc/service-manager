#! /bin/sh

clear

while true
do

    if [ "$1" = "--test" ] 
    then
        MY_PATH="`dirname \"$0\"`"
        sm --status --config $MY_PATH/../test/conf > /tmp/smstatus.txt 2>&1
    else
        sm --status > /tmp/smstatus.txt 2>&1
    fi

    clear
    cat /tmp/smstatus.txt
    sleep 2
done
