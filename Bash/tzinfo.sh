#!/bin/bash

tzinfo=$(timedatectl | grep "Time zone" | awk '{print $3}')

if [ "$tzinfo" == "Asia/Colombo" ]; then
        echo "Server in correct timezone, $tzinfo"
else
        echo "Server in wrong time zone, $tzinfo"
fi