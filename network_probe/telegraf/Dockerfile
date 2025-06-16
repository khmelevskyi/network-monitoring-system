# Use the official Telegraf image
FROM telegraf:latest  

# Install sudo if not present
RUN apt-get update && apt-get install -y sudo nano net-tools

# modify 'telegraf' user and group
#RUN groupmod -g 990 telegraf && usermod -u 995 -g 990 telegraf

# Copy the monitoring scripts
COPY arp_check_mac_ip.sh /usr/local/bin/arp_check_mac_ip.sh
RUN chmod +x /usr/local/bin/arp_check_mac_ip.sh

# Switch to the telegraf user
#USER telegraf

# Set entrypoint for Telegraf
#CMD ["telegraf", "--config", "/etc/telegraf/telegraf.conf"]
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
