#!/bin/bash
arp -e | tail -n +2 | awk 'NF==5 {
    print "arp_entry,mac=" $3 ",iface=" $5 " ip=\"" $1 "\""
}'

