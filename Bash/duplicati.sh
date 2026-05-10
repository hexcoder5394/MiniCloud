#!/bin/bash

if [ -f /etc/duplicati.conf ]; then
    echo "Duplicati is installed"
else
    echo "Duplicati is not installed"
    sudo docker compose -f /home/mcadmin/minicloud/duplicati/duplicati-compose.yml up -d
fi
