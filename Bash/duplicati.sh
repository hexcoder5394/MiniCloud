#!/bin/bash

if [ -f /etc/duplicati.conf ]; then
    echo "Duplicati is installed"
else
    echo "Duplicati is not installed"
    sudo docker compose -f ../docker/duplicati-compose.yml up -d
fi
