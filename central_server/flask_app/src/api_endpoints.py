import json

import numpy as np
import pandas as pd

from src.models import public_IP_detail
from src.geoip_traceroute import enrich_ips
from src.influxdb_funcs import flux_get_recent_flows


def get_ip_details_for_grafana(ip_to_lookup, device_ip, start_time, end_time):

	if ip_to_lookup:
		print("Specific IP address to lookup by:", ip_to_lookup)
		# Query PostgreSQL to get IP detail for the specific IP
		ip_detail = public_IP_detail.query.filter_by(ip=ip_to_lookup).first()

		# if no such IP in PostgreSQL table yet, then enrich IP, add to the table and try again
		if not ip_detail:
			enrich_ips(ip_to_lookup)
			ip_detail = public_IP_detail.query.filter_by(ip=ip_to_lookup).first()

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

	if device_ip:
		tables = flux_get_recent_flows(device_ip, start_time, end_time)

		data = []
		for table in tables:
			for record in table.records:
				data.append(record.values)
		df = pd.DataFrame(data)

		print(df.head())
		print(df.tail())
		print(df.columns)

		if df.empty:
			return json.dumps({})
			
		unique_values_series = pd.concat([df['src'], df['dst']]).unique()
		unique_ips = unique_values_series.tolist()


		# Query PostgreSQL to get details for these unique IPs
		ip_details = public_IP_detail.query.filter(public_IP_detail.ip.in_(unique_ips)).all()

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


