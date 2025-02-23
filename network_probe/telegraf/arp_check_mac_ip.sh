#!/bin/bash
arp -e | tail -n +2 | awk 'NF==5 {
    print "arp_entry,ip=" $1 " mac=\"" $3 "\""
}'

