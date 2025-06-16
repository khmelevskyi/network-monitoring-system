#!/bin/sh

# Read the secret and set the environment variable
export INFLUXDB_TOKEN=$(cat /run/secrets/influxdb-token)

# Run Telegraf
exec telegraf --config /etc/telegraf/telegraf.conf
