import json
import ipaddress
from datetime import datetime, timedelta

import requests
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from src.config import IPINFO_TOKEN
from src.models import db, public_IP_detail
from src.influxdb_funcs import flux_get_unique_ip_addresses


# Set the IPInfo API endpoint
IPINFO_URL = "https://ipinfo.io/{}/json?token={}"


# Function to check if an IP is private (local)
def is_private_ip(ip):
	return ipaddress.ip_address(ip).is_private


def enrich_ips(ip_address=None):
	# get a set of already enriched ips for the last month
	one_month_ago = datetime.utcnow() - timedelta(days=30)
	recent_ips = db.session.query(public_IP_detail.ip).filter(public_IP_detail.last_updated_at >= one_month_ago).all()
	recent_ips_set = {ip[0] for ip in recent_ips}
	print("The amount of recent_ips in PostgreSQL table:", len(recent_ips_set))

	# get a list of ip addresses in InfluxDB for the last 5 minutes
	result = flux_get_unique_ip_addresses(ip_address)

	# enrich IPs that need to be enriched
	extra_ip_requests_count = 0
	enriched_ips_data = []
	for table in result:
		for record in table.records:
			public_ip = record["_value"]

			if is_private_ip(public_ip):
				continue

			if public_ip in recent_ips_set:
				extra_ip_requests_count += 1
				continue

			# Fetch GeoIP & Hostname data from ipinfo.io
			try:
				response = requests.get(IPINFO_URL.format(public_ip, IPINFO_TOKEN), timeout=5)
				data = response.json()

				country = data.get("country", None)
				city = data.get("city", None)
				region = data.get("region", None)
				loc = data.get("loc", None)  # Latitude, Longitude
				try:
					latitude, longitude = map(float, loc.split(','))
				except (ValueError, AttributeError):
					latitude, longitude = None, None
				org = data.get("org", None)
				hostname = data.get("hostname", None)
				timezone = data.get("timezone", None)
				postal = data.get("postal", None)

				if data.get("bogon") is True:
					country = "local/private"

				# don't save empty detail
				if country is None and city is None and hostname is None:
					continue

				enriched_ips_data.append({
					"ip": public_ip,
					"country": country,
					"city": city,
					"region": region,
					"latitude": latitude,
					"longitude": longitude,
					"organization": org,
					"hostname": hostname,
					"timezone": timezone,
					"postal": postal,
					"last_updated_at": datetime.utcnow()
				})

			except requests.RequestException:
				print(f"Error fetching data for IP: {public_ip}")

	print("Extra requests for IPInfo API that could have been made:", extra_ip_requests_count)

	#### SAVE/UPSERT TO POSTGRESQL
	if enriched_ips_data:
		try:
			stmt = postgresql_insert(public_IP_detail.__table__).values(enriched_ips_data)
			stmt = stmt.on_conflict_do_update(
				index_elements=['ip'],  # The primary key to check for conflicts
				set_={
					"country": stmt.excluded.country,
					"city": stmt.excluded.city,
					"region": stmt.excluded.region,
					"latitude": stmt.excluded.latitude,
					"longitude": stmt.excluded.longitude,
					"organization": stmt.excluded.organization,
					"hostname": stmt.excluded.hostname,
					"timezone": stmt.excluded.timezone,
					"postal": stmt.excluded.postal,
					"last_updated_at": stmt.excluded.last_updated_at
				}
			)
			db.session.execute(stmt)
			db.session.commit()
			print(f"Successfully updated/inserted {len(enriched_ips_data)} IP details.")
		except Exception as e:
			db.session.rollback()
			print(f"Error during bulk upsert: {e}")
	else:
		print("No new public IP details to save.")


