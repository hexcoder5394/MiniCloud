#!/bin/bash

if [ -f /etc/duplicati.conf ]; then
    echo "Postgresql is installed"
else
    echo "Postgresql is not installed"
    sudo docker compose -f /home/mcadmin/minicloud/docker/pgsql-compose.yml up -d
fi
