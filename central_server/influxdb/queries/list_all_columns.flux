from(bucket: "network-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "tail")
  |> distinct(column: "_field")
  |> group()
  |> reduce(
      identity: {all_fields: ""},
      fn: (r, accumulator) => ({
        all_fields: if accumulator.all_fields == "" then r._field else accumulator.all_fields + ", " + r._field
      })
  )
  
