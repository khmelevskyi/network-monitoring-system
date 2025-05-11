import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.models import db, Device, Anomaly_Alert
from src.influxdb_funcs import (flux_get_data_for_ip_entropy_check,
								flux_get_data_for_botnet_activity_check,
								flux_get_suricata_alerts)



def check_entropy_anomaly():
	device_ips = db.session.query(Device.local_ip_address).all()
	device_ips_set = {ip[0] for ip in device_ips}

	tables = flux_get_data_for_ip_entropy_check(device_ips_set)
	data = []
	for table in tables:
		for record in table.records:
			data.append(record.values)
	df = pd.DataFrame(data)
	print("The DF for check entropy anomaly\n", df[["src", "dst", "in_bytes"]])

	for src_ip, group in df.groupby('src'):
		total_bytes = group['in_bytes'].sum()
		# Probability distribution over dsts
		p = group.groupby('dst')['in_bytes'].sum() / total_bytes
		entropy = -np.sum(p * np.log2(p))

		print(f"Device {src_ip}:")
		print(f"  Total bytes sent: {total_bytes}")
		print(f"  Destination entropy: {entropy:.3f}")

		# Detection rule (traffic more than 1 MB and entropy less than 1)
		if total_bytes > 1_048_576 and entropy < 1.0:
			print("  ⚠️  Potential data exfiltration detected")

			total_mbytes = round(total_bytes / 1024 / 1024, 2)
			recent_time_threshold = datetime.utcnow() - timedelta(seconds=3600)
			existing = Anomaly_Alert.query.filter_by(
				alert_type="ips_entropy_anomaly",
				src_ip=src_ip
			).filter(Anomaly_Alert.alert_time >= recent_time_threshold).first()

			if not existing:
				new_alert = Anomaly_Alert(
					alert_type="ips_entropy_anomaly",
					classification="Low Entropy in Destination IPs",
					description=f"Low entropy (={entropy:.2f}) with high outgoing traffic (~{total_mbytes} MB)\n"\
								"High volume of outgoing traffic to a limited number of destination IPs, "\
								"indicating possible DDoS or malware communication",
					priority=2,
					alert_time=group["_time"],
					src_ip=src_ip,
					router_mac=group['rpi_mac'],
					router_public_ip=group['rpi_public_ip']
				)
				db.session.add(new_alert)
				db.session.commit()



def check_botnet_activity():
	device_ips = db.session.query(Device.local_ip_address).all()
	device_ips_set = {ip[0] for ip in device_ips}

	tables = flux_get_data_for_botnet_activity_check(device_ips_set)
	data = []
	for table in tables:
		for record in table.records:
			data.append(record.values)
	df = pd.DataFrame(data)
	print("The DF for check botnet activity\n", df[["src", "dst"]])

	# Detect suspicious periodic communication per (src, dst)
	for (src, dst), group in df.groupby(['src', 'dst']):
		times = group['_time'].sort_values().values
		if len(times) < 10:
			continue  # not enough data

		# Convert to seconds
		times_sec = [t.astype('int64') // 1_000_000_000 for t in times]
		deltas = np.diff(times_sec)

		if len(deltas) >= 10: # connections between src and dst happened at least 10 times within last 1 hour
			stddev = np.std(deltas)
			mean = np.mean(deltas)
			print(f"{src} -> {dst} | Mean interval: {mean}s | Stddev: {stddev:.2f}s\n")

			if stddev < 30 and mean > 60:  # at least every ~60s with low variation of less than 30 seconds
				print(f"{src} -> {dst}  ⚠️  Suspicious periodic communication detected\n")
				recent_time_threshold = datetime.utcnow() - timedelta(seconds=3600)
				existing = Anomaly_Alert.query.filter_by(
					alert_type="potential_botnet_activity",
					src_ip=src,
					dst_ip=dst
				).filter(Anomaly_Alert.alert_time >= recent_time_threshold).first()

				if not existing:
					new_alert = Anomaly_Alert(
						alert_type="potential_botnet_activity",
						classification="Botnet-like Behavior",
						description=f"Suspicious periodic communication (mean={mean:.2f}s, stddev={stddev:.2f}s)\n"\
									"Device behavior resembles known botnet patterns "\
									"(e.g., frequent small outbound flows to many IPs)",
						priority=1,
						alert_time=group["_time"],
						src_ip=src,
						dst_ip=dst,
						router_mac=group['rpi_mac'],
						router_public_ip=group['rpi_public_ip']
					)
					db.session.add(new_alert)
					db.session.commit()


def check_suricata_alerts():
	tables = flux_get_suricata_alerts()
	new_alerts = []

	for table in tables:
		for record in table.records:
			r = record.values
			alert_time = r["_time"]
			alert_type = r.get("_measurement")
			classification = r.get("classification")
			description = r.get("alert")
			priority = r["priority"]
			src_ip = r.get("src")
			src_port = r.get("src_port")
			dst_ip = r.get("dst")
			dst_port = r.get("dst_port")
			protocol = r.get("protocol")
			router_mac = r.get("rpi_mac")
			router_public_ip = r.get("rpi_public_ip")

			existing = Anomaly_Alert.query.filter_by(
				alert_time=alert_time,
				alert_type=alert_type,
				src_ip=src_ip,
				dst_ip=dst_ip,
				router_mac=router_mac
			).first()

			if not existing:
				new_alerts.append(Anomaly_Alert(
					alert_time=alert_time,
					alert_type=alert_type,
					classification=classification,
					description=description,
					priority=priority,
					src_ip=src_ip,
					src_port=src_port,
					dst_ip=dst_ip,
					dst_port=dst_port,
					protocol=protocol,
					router_mac=router_mac,
					router_public_ip=router_public_ip
				))

	if new_alerts:
		db.session.add_all(new_alerts)
		db.session.commit()
		print(f"Added {len(new_alerts)} new alerts to the PostgreSQL anomaly_alerts table")



def check_all_anomalies():
	check_entropy_anomaly()
	check_botnet_activity()
	check_suricata_alerts()