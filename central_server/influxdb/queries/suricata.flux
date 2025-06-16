from(bucket: "network-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop) //start: v.timeRangeStart, stop: v.timeRangeStop // start: 2025-02-21T20:31:00Z
  |> filter(fn: (r) => r["_measurement"] == "tail")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "_field", "_value", "src_port", "dest_port", "icmp_type", "icmp_code",
                    "flow_bytes_toclient", "flow_bytes_toserver", "flow_pkts_toclient", "flow_pkts_toserver",

                    "alert_gid", "alert_rev", "alert_severity", "alert_signature_id", "fileinfo_size", "http_http_port",
                    "http_length", "http_status",

                    "stats_decoder_max_mac_addrs_dst", "stats_decoder_max_mac_addrs_src",
                    
                    "stats_app_layer_tx_dns_tcp", "stats_detect_engines_0_rules_failed", "stats_detect_engines_0_rules_loaded",
                    "stats_decoder_pkts", "stats_decoder_udp", "stats_decoder_tcp", "stats_detect_alert", "stats_uptime"])

//   |> filter(fn: (r) => r["src_port"] == 33482)
//   |> filter(fn: (r) => exists(r["alert_gid"]))
