# Use the official Telegraf image
FROM telegraf:latest  

# Install sudo if not present
RUN apt-get update && apt-get install -y sudo && apt-get install -y nano  

# modify 'telegraf' user and group
RUN groupmod -g 990 telegraf && usermod -u 995 -g 990 telegraf

# Copy the process monitoring script
COPY process_monitor.sh /usr/local/bin/process_monitor.sh  
RUN chmod +x /usr/local/bin/process_monitor.sh  

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
