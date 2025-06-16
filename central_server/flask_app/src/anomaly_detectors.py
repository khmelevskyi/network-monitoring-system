import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.ssh_client import ssh_block_device
from src.models import db, Device, Anomaly_Alert, Public_IP_Detail, Custom_IP_List_Entry
from src.influxdb_funcs import (flux_get_data_for_ip_entropy_check,
								flux_get_data_for_botnet_activity_check,
								flux_get_suricata_alerts,
								flux_get_recent_flows_for_anomaly_checks)


def is_ip_whitelisted(ip):
	return Custom_IP_List_Entry.query.filter_by(ip_address=ip, label='whitelist').first() is not None


def check_entropy_anomaly():
	device_ips = db.session.query(Device.local_ip_address).all()
	device_ips_set = {ip[0] for ip in device_ips}

	tables = flux_get_data_for_ip_entropy_check(device_ips_set)
	data = []
	for table in tables:
		for record in table.records:
			data.append(record.values)
	df = pd.DataFrame(data)

	if df.empty:
		print("No data to check for entropy anomaly")
		return None

	# print("The DF for check entropy anomaly\n", df[["src", "dst", "in_bytes"]])

	for src_ip, group in df.groupby('src'):
		total_bytes = group['in_bytes'].sum()
		# Probability distribution over dsts
		p = group.groupby('dst')['in_bytes'].sum() / total_bytes
		entropy = -np.sum(p * np.log2(p))

		# print(f"Device {src_ip}:")
		# print(f"  Total bytes sent: {total_bytes}")
		# print(f"  Destination entropy: {entropy:.3f}")

		# Detection rule (traffic more than 1 MB and entropy less than 1)
		if total_bytes > 1_048_576 and entropy < 1.0:
			print("  ⚠️  Potential data exfiltration detected")

			# Skip if all of the dst IPs are whitelisted
			if all(is_ip_whitelisted(dst_ip) for dst_ip in group['dst'].unique()):
				print(f"Whitelisted IPs for {src_ip}: {[dst_ip for dst_ip in group['dst'].unique()]}")
				continue

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
					alert_time=group["_time"].max(),
					src_ip=src_ip,
					router_mac=group['rpi_mac'].iloc[0],
					router_public_ip=group['rpi_public_ip'].iloc[0]
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

	if df.empty:
		print("No data to check for botnet activity")
		return None

	# print("The DF for check botnet activity\n", df[["src", "dst"]])

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
			# print(f"{src} -> {dst} | Mean interval: {mean}s | Stddev: {stddev:.2f}s\n")

			if stddev < 30 and mean > 60:  # at least every ~60s with low variation of less than 30 seconds
				print(f"{src} -> {dst}  ⚠️  Suspicious periodic communication detected\n")

				# Skip if dst IP is whitelisted
				if is_ip_whitelisted(dst):
					print(f"Whitelisted IP: {dst}")
					continue

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
						priority=2,
						alert_time=group["_time"].max(),
						src_ip=src,
						dst_ip=dst,
						router_mac=group['rpi_mac'].iloc[0],
						router_public_ip=group['rpi_public_ip'].iloc[0]
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
			alert_type = "suricata"
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

			# Skip if dst IP is whitelisted
			if is_ip_whitelisted(src_ip) or is_ip_whitelisted(dst_ip):
				print(f"Whitelisted IP: {src_ip} or {dst_ip}")
				continue

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



def check_blacklisted_connections():
	device_ips = db.session.query(Device.local_ip_address).all()
	device_ips_set = {ip[0] for ip in device_ips}

	# Get all blacklisted IPs into a set
	blacklisted_ips = {e.ip_address for e in Custom_IP_List_Entry.query.filter_by(label='blacklist').all()}

	if not blacklisted_ips:
		return

	tables = flux_get_recent_flows_for_anomaly_checks(device_ips_set)

	for table in tables:
		for record in table.records:
			r = record.values
			src = r.get('src')
			dst = r.get('dst')
			if dst in blacklisted_ips:
				recent_time_threshold = datetime.utcnow() - timedelta(seconds=3600) # 3600
				existing = Anomaly_Alert.query.filter_by(
					alert_type="blacklisted_ip",
					src_ip=src,
					dst_ip=dst
				).filter(Anomaly_Alert.alert_time >= recent_time_threshold).first()

				if not existing:
					new_alert = Anomaly_Alert(
						alert_type="blacklisted_ip",
						classification="Connection to Blacklisted IP",
						description=f"Device {src} connected to blacklisted IP {dst}",
						priority=1,
						alert_time=r["_time"],
						src_ip=src,
						dst_ip=dst,
						router_mac=r['rpi_mac'],
						router_public_ip=r['rpi_public_ip']
					)
					db.session.add(new_alert)
					db.session.commit()

					ssh_block_device(rpi_mac=r["rpi_mac"], device_local_ip=src)


def check_for_ips_from_restricted_countried():
	# Define country lists
	banned_countries = {"RU": "Russia", "KP": "North Korea", "IR": "Iran", "BY": "Belarus"}
	suspicious_countries = {"CN": "China", "SY": "Syria"}

	# Get all local device IPs
	device_ips = db.session.query(Device.local_ip_address).all()
	device_ips_set = {ip[0] for ip in device_ips}

	# Get flows from the last 5 minutes
	tables = flux_get_recent_flows_for_anomaly_checks(device_ips_set)

	for table in tables:
		for record in table.records:
			r = record.values
			src_ip = r.get('src')       # local device
			dst_ip = r.get('dst')       # public IP

			# Get country info
			public_ip_detail = Public_IP_Detail.query.filter_by(ip=dst_ip).first()
			if not public_ip_detail or not public_ip_detail.country:
				continue

			country = public_ip_detail.country.strip()

			if country not in suspicious_countries.keys() and country not in banned_countries.keys():
				continue

			# Check if alert already exists
			recent_time_threshold = datetime.utcnow() - timedelta(seconds=3600)
			existing = Anomaly_Alert.query.filter_by(
				alert_type="geoip_country_restricted",
				src_ip=src_ip
			).filter(Anomaly_Alert.alert_time >= recent_time_threshold).first()

			if existing:
				continue

			is_banned_country = country in banned_countries

			new_alert = Anomaly_Alert(
				alert_type="geoip_country_restricted",
				classification="Communication with Restricted Country",
				description=f"Device {src_ip} communicated with IP {dst_ip} in {country}",
				priority=1 if is_banned_country else 3,
				alert_time=r["_time"],
				src_ip=src_ip,
				dst_ip=dst_ip,
				router_mac=r['rpi_mac'],
				router_public_ip=r['rpi_public_ip']
			)
			db.session.add(new_alert)
			db.session.commit()

			print(f"🚨 Alert: {src_ip} → {dst_ip} in {country} ({'BANNED' if is_banned_country else 'SUSPICIOUS'})")

			if is_banned_country:
				ssh_block_device(rpi_mac=r["rpi_mac"], device_local_ip=src_ip)



def check_all_anomalies():
	check_entropy_anomaly()
	check_botnet_activity()
	check_suricata_alerts()
	check_blacklisted_connections()
	check_for_ips_from_restricted_countried()