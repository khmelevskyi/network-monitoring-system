#!/bin/bash

# File to store connections
CONNECTIONS_FILE="/tmp/network_connections.txt"

# Function to get current connections
get_current_connections() {
    sudo ss -tunap | awk 'NR>1 {
        pid_prog=$7
        split(pid_prog, a, ",")
        pid=a[2]
        prog=a[1]
        if (pid == "") pid="N/A"
        if (prog == "") prog="N/A"
        gsub(/users:\(\(/, "", prog)
        gsub(/\)\)/, "", prog)
        split($5, src, ":")
        split($6, dst, ":")
        printf "%s,%s,%s,%s,%s,%s,%s,%s\n", 
            pid, prog, src[1], src[2], dst[1], dst[2], $1, $2
    }'
}



# Initialize connections file if it doesn't exist
touch "$CONNECTIONS_FILE"

# Add header line if file is empty
if [ ! -s "$CONNECTIONS_FILE" ]; then
    echo "PID,Process,Source IP,Source Port,Destination IP,Destination Port,Protocol,Status" > "$CONNECTIONS_FILE"
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
