import json
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.exc import IntegrityError

from src.models import db, Router, Device, Public_IP_Detail
from src.ip_details_enrichment import enrich_ips
from src.influxdb_funcs import (
	flux_get_recent_flows,
	flux_get_actual_routers,
	flux_get_actual_devices
)


def api_update_routers():
	result = flux_get_actual_routers()

	# Process results
	for table in result:
		for record in table.records:
			rpi_mac = record.values.get("rpi_mac")
			rpi_description = record.values.get("rpi_description")
			rpi_public_ip = record.values.get("rpi_public_ip")
			rpi_local_ip = record.values.get("rpi_local_ip")
			rpi_ssh_username = record.values.get("rpi_ssh_username")
			last_seen_online = record.values.get("_time")

			# Find the router
			router = Router.query.filter_by(mac_address=rpi_mac).first()
			if router:
				# Update existing router
				router.description = rpi_description
				router.public_ip_address = rpi_public_ip
				router.local_ip_address = rpi_local_ip
				router.ssh_username = rpi_ssh_username
				router.last_seen_online = last_seen_online
			else:
				# Add new Router
				new_router = Router(
					mac_address=rpi_mac,
					description=rpi_description,
					public_ip_address=rpi_public_ip,
					local_ip_address=rpi_local_ip,
					ssh_username=rpi_ssh_username,
					last_seen_online=last_seen_online
				)
				db.session.add(new_router)

			try:
				db.session.commit()
			except IntegrityError:
				db.session.rollback()
				print(f"Error updating router {rpi_mac}")

	return json.dumps({"status": "success", "last_checked_routers": str(datetime.utcnow())})


def api_update_devices():
	result = flux_get_actual_devices()

	# Process results
	for table in result:
		for record in table.records:
			rpi_mac = record.values.get("rpi_mac")
			device_mac = record.values.get("mac")
			ip_address = record.values.get("_value")
			last_seen_online = record.values.get("_time")

			# Find the router
			router = Router.query.filter_by(mac_address=rpi_mac).first()
			if router:
				# Check if device exists
				device = Device.query.filter_by(mac_address=device_mac, router_id=router.id).first()
				if device:
					# Update existing device
					device.local_ip_address = ip_address
					device.last_seen_online = last_seen_online
				else:
					# Add new device
					new_device = Device(
						mac_address=device_mac,
						local_ip_address=ip_address,
						router_id=router.id,
						last_seen_online=last_seen_online
					)
					db.session.add(new_device)

				try:
					db.session.commit()
				except IntegrityError:
					db.session.rollback()
					print(f"Error updating device {device_mac} for router {rpi_mac}")

	return json.dumps({"status": "success", "last_checked_devices": str(datetime.utcnow())})


def api_get_ip_details(ip_to_lookup, device_ips, start_time, end_time):

	if ip_to_lookup: # if needed IP detail only for one IP address
		print("Specific IP address to lookup by:", ip_to_lookup)
		# Query PostgreSQL to get IP detail for the specific IP
		ip_detail = Public_IP_Detail.query.filter_by(ip=ip_to_lookup).first()

		# if no such IP in PostgreSQL table yet, then enrich IP, add to the table and try again
		if not ip_detail:
			enrich_ips(ip_to_lookup)
			ip_detail = Public_IP_Detail.query.filter_by(ip=ip_to_lookup).first()

		# Prepare the result to be returned as JSON
		result ={
			"ip": ip_detail.ip,
			"country": ip_detail.country,
			"city": ip_detail.city,
			"region": ip_detail.region,
			"latitude": ip_detail.latitude,
			"longitude": ip_detail.longitude,
			"organization": ip_detail.organization,
			"hostname": ip_detail.hostname,
			"timezone": ip_detail.timezone,
			"postal": ip_detail.postal
		}

		return json.dumps(result)

	# Grafana passes either one device_ip
	# or a list of all device_ips if the option 'ALL' is chosen
	# So, we always have device_ip variable with some value
	tables = flux_get_recent_flows(device_ips, start_time, end_time)

	data = []
	for table in tables:
		for record in table.records:
			data.append(record.values)
	df = pd.DataFrame(data)

	print("The DF head for returning IP details\n", df.head())
	print("The DF tail for returning IP details\n", df.tail())

	if df.empty:
		return json.dumps({})
		
	unique_values_series = pd.concat([df['src'], df['dst']]).unique()
	unique_ips = unique_values_series.tolist()


	# Query PostgreSQL to get details for these unique IPs
	ip_details = Public_IP_Detail.query.filter(Public_IP_Detail.ip.in_(unique_ips)).all()

	# Prepare the result to be returned as JSON
	results = []
	for detail in ip_details:
		results.append({
			"ip": detail.ip,
			"country": detail.country,
			"city": detail.city,
			"region": detail.region,
			"latitude": detail.latitude,
			"longitude": detail.longitude,
			"organization": detail.organization,
			"hostname": detail.hostname,
			"timezone": detail.timezone,
			"postal": detail.postal
		})

	return json.dumps(results)


