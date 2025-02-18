#!/bin/bash

echo "Deploying configuration files..."

# Copy Telegraf configuration
#sudo cp network_probe/telegraf/telegraf.conf /etc/telegraf/telegraf.conf

# Copy Suricata configuration
sudo suricata-update
sudo cp network_probe/suricata/rules/custom.rules /etc/suricata/rules/custom.rules
sudo cp network_probe/suricata/suricata.yaml /etc/suricata/suricata.yaml
sudo suricata -T -c /etc/suricata/suricata.yaml

# Copy file to monitor processes and ports which they use
#sudo cp network_probe/telegraf/process_monitor.sh ~/process_monitor.sh
echo "telegraf ALL=(ALL) NOPASSWD: /home/eugene/process_monitor.sh" | sudo tee /etc/sudoers.d/010_telegraf_user

# Restart services to apply changes
echo "Restarting services..."
#sudo systemctl restart telegraf
sudo systemctl restart suricata

echo "Deployment complete!"
