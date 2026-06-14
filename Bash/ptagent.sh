#!/bin/bash

if [ -f /etc/portainer.conf ]; then
    echo "Portainer is installed"
else
    echo "Portainer is not installed"
    sudo docker compose -f /home/mcadmin/minicloud/docker/pa-compose.yml up -d
fi