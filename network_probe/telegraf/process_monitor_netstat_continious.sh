#!/bin/bash

# File to store connections
CONNECTIONS_FILE="/tmp/network_netstat_connections.txt"

# Function to get current connections
get_current_connections() {
    netstat -tunap | awk 'NR>2 {
        pid="N/A"; prog="N/A"; status="N/A"
        if (NF == 6 || ($7 == "--fo" || $7 == "r") ) {
            split($5, remote, ":")
            status="-"
            split($6, a, "/")
            pid=a[1]
            prog=a[2]
        } else if (NF >= 7) {
            split($5, remote, ":")
            status=$6
            split($7, a, "/")
            pid=a[1]
            prog=a[2]
        }
        split($4, local, ":")
        if (pid == "-") pid="N/A"
        if (prog == "") prog="N/A"
        if (status == "-") status="N/A"
        printf "%s,%s,%s,%s,%s,%s,%s,%s\n", 
            pid, prog, $4, local[2], $5, remote[2], status, $1
    }'
}

get_current_connections2() {
    netstat -tupl | awk 'NR>2 {
        printf "%s,%s,%s,%s,%s,%s\n", 
            $1, $2, $3, $4, $5, $6
    }'
}
# Initialize connections file if it doesn't exist
touch "$CONNECTIONS_FILE"

# Add header line if file is empty
if [ ! -s "$CONNECTIONS_FILE" ]; then
    echo "PID,Process,Source IP,Source Port,Destination IP,Destination Port,Status,Protocol" > "$CONNECTIONS_FILE"
fi

# Print initial text
echo "Updated list of all observed connections:"
cat "$CONNECTIONS_FILE" | column -t -s ','


# Variable to track if list was updated
list_updated=false

while true; do
    # Get current connections
    current=$(get_current_connections)

    # Compare with existing connections and add new ones
    while IFS= read -r line; do
        if ! grep -Fq "$line" "$CONNECTIONS_FILE"; then
            echo "$line" >> "$CONNECTIONS_FILE"
            list_updated=true
        fi
    done <<< "$current"

    # If list was updated, clear screen and print all connections
    if [ "$list_updated" = true ]; then
        clear
        echo "Updated list of all observed connections:"
        cat "$CONNECTIONS_FILE" | column -t -s ','
        list_updated=false
    fi

    # Wait for 1 seconds before next check
    sleep 1
done
