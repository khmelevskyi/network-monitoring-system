

def convert_bytes(in_bytes):
	if in_bytes < 1024:
		traffic_value = f"{int(in_bytes)} B"
	elif in_bytes >= 1024 and in_bytes < 1024**2:
		traffic_value = f"{int(in_bytes / 1024)} KB"
	elif in_bytes >= 1024**2 and in_bytes < 1024**3:
		traffic_value = f"{int(in_bytes / 1024**2)} MB"
	elif in_bytes >= 1024**3:
		traffic_value = f"{round(in_bytes / 1024**3, 2)} GB"
	return traffic_value