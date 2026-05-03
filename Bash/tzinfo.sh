#!/bin/bash

tzinfo=$(timedatectl | grep "Time zone" | awk '{print $3}')

if [ "$tzinfo" == "Asia/Colombo" ]; then
        echo "Server in correct timezone, $tzinfo"
else
        timedatectl set-timezone Asia/Colombo
        echo "Timezone updated to correct timezone"
fi
