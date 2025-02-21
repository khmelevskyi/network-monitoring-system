#!/bin/bash

influx bucket create -n network-data -o network-monitoring
influx auth create -o network-monitoring -u admin --read-bucket network-data --write-bucket network-data --token all_access_api_token
