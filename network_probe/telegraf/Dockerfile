# Use the official Telegraf image
FROM telegraf:latest  

# Install sudo if not present
RUN apt-get update && apt-get install -y sudo nano net-tools

# modify 'telegraf' user and group
RUN groupmod -g 990 telegraf && usermod -u 995 -g 990 telegraf

# Copy the process monitoring scripts
COPY process_monitor.sh /usr/local/bin/process_monitor.sh  
RUN chmod +x /usr/local/bin/process_monitor.sh
COPY arp_check_mac_ip.sh /usr/local/bin/arp_check_mac_ip.sh
RUN chmod +x /usr/local/bin/arp_check_mac_ip.sh

# Grant Telegraf permission to execute the script
RUN echo "telegraf ALL=(ALL) NOPASSWD: /usr/local/bin/process_monitor.sh" | tee /etc/sudoers.d/010_telegraf_user  

# Copy Telegraf configuration
COPY telegraf.conf /etc/telegraf/telegraf.conf  

# Switch to the telegraf user
#USER telegraf

# Set entrypoint for Telegraf
#CMD ["telegraf", "--config", "/etc/telegraf/telegraf.conf"]
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
