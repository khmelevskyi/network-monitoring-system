# Use a base image with Suricata
FROM jasonish/suricata:latest  

# Install sudo (if not included in base image)
RUN apt-get update && apt-get install -y sudo  

# Update Suricata rules
RUN suricata-update  

# Copy Suricata configuration
COPY suricata.yaml /etc/suricata/suricata.yaml  
COPY rules/custom.rules /etc/suricata/rules/custom.rules  

# Validate Suricata configuration
RUN suricata -T -c /etc/suricata/suricata.yaml  

# Set entrypoint to run Suricata
CMD ["suricata", "-i", "wlan0", "--pcap"]
