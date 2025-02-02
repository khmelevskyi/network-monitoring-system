#!/bin/bash

echo "Deploying configuration files..."

# Copy Telegraf configuration
#sudo cp network_probe/telegraf/telegraf.conf /etc/telegraf/telegraf.conf

# Copy Suricata configuration
sudo suricata-update
sudo cp network_probe/suricata/rules/custom.rules /etc/suricata/rules/custom.rules
sudo cp network_probe/suricata/suricata.yaml /etc/suricata/suricata.yaml
sudo suricata -T -c /etc/suricata/suricata.yaml

# Copy nProbe configuration
#sudo cp network_probe/nprobe/nprobe.conf /etc/nprobe/nprobe.conf

# Restart services to apply changes
echo "Restarting services..."
#sudo systemctl restart telegraf
sudo systemctl restart suricata
#sudo systemctl restart nprobe

echo "Deployment complete!"
