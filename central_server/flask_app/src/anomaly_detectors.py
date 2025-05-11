import numpy as np
import pandas as pd

from src.influxdb_funcs import (flux_get_data_for_ip_entropy_check,
								flux_get_data_for_botnet_activity_check)



def check_entropy_anomaly():
	tables = flux_get_data_for_ip_entropy_check()
	data = []
	for table in tables:
		for record in table.records:
			data.append(record.values)
	df = pd.DataFrame(data)
	print("The DF for check entropy anomaly\n", df)

	for src_ip, group in df.groupby('src'):
		total_bytes = group['in_bytes'].sum()
		# Probability distribution over dsts
		p = group.groupby('dst')['in_bytes'].sum() / total_bytes
		entropy = -np.sum(p * np.log2(p))

		print(f"Device {src_ip}:")
		print(f"  Total bytes sent: {total_bytes}")
		print(f"  Destination entropy: {entropy:.3f}")
		# print(p)

		# Detection rule (traffic more than 1 MB and entropy less than 1)
		if total_bytes > 1_048_576 and entropy < 1.0:
			print("  ⚠️  Potential data exfiltration detected")



def check_botnet_activity():
	tables = flux_get_data_for_botnet_activity_check()
	data = []
	for table in tables:
		for record in table.records:
			data.append(record.values)
	df = pd.DataFrame(data)
	print("The DF for check botnet activity\n", df)

	text_result = {}

	# Detect suspicious periodic communication per (src, dst)
	for (src, dst), group in df.groupby(['src', 'dst']):
		times = group['_time'].sort_values().values
		if len(times) < 10:
			continue  # not enough data

		# Convert to seconds
		times_sec = [t.astype('int64') // 1_000_000_000 for t in times]
		deltas = np.diff(times_sec)

		if len(deltas) > 5:
			stddev = np.std(deltas)
			mean = np.mean(deltas)
			text_result[f"{src} -> {dst}"] = f"{src} -> {dst} | Mean interval: {mean}s | Stddev: {stddev:.2f}s\n"

			if dst == "90.130.70.73" or dst == "224.0.0.252":
				text_result[f"{src} -> {dst}"] += f"{times_sec} | {deltas}"

			if stddev < 30 and mean > 5:  # e.g. every ~10s with low variation
				text_result[f"{src} -> {dst}"]  += "  ⚠️  Suspicious periodic communication detected\n"

	return text_result



