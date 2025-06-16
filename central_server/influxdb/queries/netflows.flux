from(bucket: "network-data")
  |> range(start: -1h)  
  |> filter(fn: (r) => r._measurement == "netflow")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> filter(fn: (r) => r.src == "192.168.4.31" or r.dst == "192.168.4.31") 
  |> keep(columns: ["_time", "direction", "dst", "dst_port", "flow_end_reason", "in_bytes",
                    "in_packets", "in_snmp", "protocol", "src", "src_port",
//                     "_start", "_stop", "_measurement", "host", "source", "version", "first_switched", "last_switched",
//                     "out_snmp", "src_tos", "tcp_flags", "ip_version", "icmp_code", "icmp_type"
                    ])

//   |> group(columns: ["src", "dst"])  // Preserve src and dst
//   |> aggregateWindow(every: 10s, fn: sum, column: "in_bytes") 
//   |> map(fn: (r) => ({ 
//       _time: r._time, 
//       in_bytes: r.in_bytes / 1024.0, 
//       direction: if r.src == "192.168.0.107" then "outgoing" else "incoming"
//   }))
