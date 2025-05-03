from collections import Counter
import numpy as np
import time
import pandas as pd

from src.influxdb_funcs import flux_get_data_for_port_scanning_detection


tables = flux_get_data_for_port_scanning_detection()
data = []
for table in tables:
    for record in table.records:
        data.append(record.values)
df = pd.DataFrame(data)
print(df)


def entropy(port_counts):
	total = sum(port_counts.values())
	probs = [v / total for v in port_counts.values()]
	return -sum(p * np.log2(p) for p in probs)

entropy_scores = []
for ip in df["src"].unique():
	ports = df[df["src"] == ip]["dst_port"]
	counts = Counter(ports)
	e = entropy(counts)
	entropy_scores.append((ip, e))

for ip, e in entropy_scores:
	print(ip, e)
	if e > 3.5:  # threshold to tune
		print(f"Possible port scan from {ip} (entropy={e})")
