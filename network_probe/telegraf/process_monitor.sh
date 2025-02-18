#!/bin/bash

# Define the measurement name
MEASUREMENT="process_info"

# Get the process-port mapping using netstat
netstat -tunapl 2>/dev/null | awk 'NR>2 { 
    split($7, pidproc, "/"); 
    if (length(pidproc) > 1) 
        print "process_info,process=" pidproc[2] ",protocol=" $1 " local_addr=\"" $4 "\",remote_addr=\"" $5 "\",state=\"" $6 "\""
}'

