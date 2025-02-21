#!/bin/sh

# Read the secret and set the environment variable
export INFLUX_TOKEN=$(cat /run/secrets/influx_token)
echo "export INFLUX_TOKEN=$INFLUX_TOKEN" >> /etc/profile

# Run Telegraf
exec telegraf --config /etc/telegraf/telegraf.conf
