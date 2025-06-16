# Use an official Ubuntu runtime as a parent image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install Suricata and dependencies
RUN apt-get update && apt-get install -y \
    suricata \
    jq \
    nano \
    libpcap-dev \
    libnet1-dev \
    libyaml-dev \
    libjansson-dev \
    libpcre3-dev \
    libmagic-dev \
    libcap-ng-dev \
    libnetfilter-queue-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Suricata configuration file
COPY suricata.yaml /etc/suricata/suricata.yaml

# Copy custom rules
COPY rules/custom.rules /etc/suricata/rules/custom.rules

# Create necessary directories
RUN mkdir -p /var/log/suricata /var/run/suricata

# Set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports (adjust as needed)
EXPOSE 1514

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]


