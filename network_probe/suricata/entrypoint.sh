#!/bin/bash

# This command sets the script to exit immediately if any command exits with a non-zero status.
# It's a safety measure to ensure that if any part of the script fails, the entire script stops executing.
set -e

# Update Suricata rules
suricata-update

# Verify Suricata configuration
suricata -T -c /etc/suricata/suricata.yaml -v

# If verification passes, run Suricata
exec suricata -c /etc/suricata/suricata.yaml "$@"
