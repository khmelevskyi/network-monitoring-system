from(bucket: "network-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "process_info")
  |> pivot(rowKey:["_time", "process", "protocol"], columnKey: ["_field"], valueColumn: "_value")
  |> filter(fn: (r) => r.process != "telegraf")
  |> group(columns: ["local_addr", "process"])  // Group by local_addr + process
  |> last(column: "_time")  // Get only the last record per group
