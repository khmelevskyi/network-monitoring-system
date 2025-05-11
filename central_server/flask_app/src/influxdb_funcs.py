from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from src.config import (INFLUXDB_HOST, INFLUXDB_PORT,
	INFLUXDB_ORG, INFLUXDB_TOKEN, INFLUXDB_BUCKET)


INFLUXDB_URL = f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}"


def execute_flux_query(query):
	with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
		tables = client.query_api().query(query)
		return tables


def flux_get_actual_routers():
	flux_query = f'''
		from(bucket: "{INFLUXDB_BUCKET}")
			|> range(start: -15m)
			|> filter(fn: (r) => r._measurement == "arp_entry")
			|> keep(columns: ["rpi_mac", "rpi_description", "rpi_public_ip", "rpi_local_ip", "rpi_ssh_username", "_time"])
			|> last(column: "_time")
	'''

	result = execute_flux_query(flux_query)
	return result


def flux_get_actual_devices():
	flux_query = f'''
		from(bucket: "{INFLUXDB_BUCKET}")
			|> range(start: -15m)
			|> filter(fn: (r) => r._measurement == "arp_entry" and r.iface == "wlan0")
			|> keep(columns: ["_time", "_field", "_value", "mac", "rpi_mac"])
			|> last(column: "_time")
	'''

	result = execute_flux_query(flux_query)
	return result


def flux_get_unique_ip_addresses(ip_address):
	if not ip_address:
		flux_query = f'''
			from(bucket: "{INFLUXDB_BUCKET}")
				|> range(start: -5m)
				|> filter(fn: (r) => r["_measurement"] == "netflow")
				|> filter(fn: (r) => r["_field"] == "src" or r["_field"] == "dst")
				|> keep(columns: ["_value"])
				|> distinct(column: "_value")
			'''

	elif ip_address:
		flux_query = f'''
			from(bucket: "{INFLUXDB_BUCKET}")
				|> range(start: -5m)
				|> filter(fn: (r) => r["_measurement"] == "netflow")
				|> filter(fn: (r) => r["_field"] == "src" or r["_field"] == "dst")
				|> filter(fn: (r) => r["_value"] == "{ip_address}")
				|> keep(columns: ["_value"])
				|> distinct(column: "_value")
			'''

	result = execute_flux_query(flux_query)
	return result


def flux_get_data_for_ip_entropy_check(device_ips_set):
	flux_ip_list = "[" + ", ".join(['"' + ip + '"' for ip in device_ips_set]) + "]"

	flux_query = f'''
		from(bucket: "network-data")
			|> range(start: -30m)
			|> filter(fn: (r) => r._measurement == "netflow")
			|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
			|> filter(fn: (r) => contains(value: r.src, set: {flux_ip_list})) // Filter by list of src IPs
			|> group(columns: ["src", "dst", "rpi_mac", "rpi_public_ip"])
			|> sum(column: "in_bytes")  // total per (src, dst)
	'''

	result = execute_flux_query(flux_query)
	return result


def flux_get_data_for_botnet_activity_check(device_ips_set):
	flux_ip_list = "[" + ", ".join(['"' + ip + '"' for ip in device_ips_set]) + "]"

	flux_query = f'''
		import "date"
		from(bucket: "network-data")
			|> range(start: -1h)
			|> filter(fn: (r) => r._measurement == "netflow")
			|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
			|> filter(fn: (r) => contains(value: r.src, set: {flux_ip_list})) // Filter by list of src IPs
			|> map(fn: (r) => ({{ r with _time: date.truncate(t: r._time, unit: 1s)}}))
			|> keep(columns: ["_time", "src", "dst", "rpi_mac", "rpi_public_ip"])
			|> group(columns: ["_time", "src", "dst", "rpi_mac", "rpi_public_ip"])
			|> last(column: "_time")
			|> sort(columns: ["src", "dst", "_time"])
	'''

	result = execute_flux_query(flux_query)
	return result


def flux_get_recent_flows(device_ips_set, start_time, end_time):
	ip_list = [ip.strip() for ip in device_ips_set.strip('{}').split(',')]
	flux_ip_list = "[" + ", ".join(['"' + ip + '"' for ip in ip_list]) + "]"

	flux_query = f'''
		from(bucket: "{INFLUXDB_BUCKET}")
			|> range(start: {start_time}, stop: {end_time})
			|> filter(fn: (r) => r._measurement == "netflow")
			|> filter(fn: (r) => r._field == "src" or r._field == "dst")
			|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
			|> filter(fn: (r) => contains(value: r.dst, set: {flux_ip_list}) or contains(value: r.src, set: {flux_ip_list}))
			|> keep(columns: ["dst", "src"])
		'''

	result = execute_flux_query(flux_query)
	return result



def flux_get_suricata_alerts():
	flux_query = f'''
		from(bucket: "network-data")
			|> range(start: today())
			|> filter(fn: (r) => r["_measurement"] == "suricata_alerts")
			|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
			|> group()
  
	'''

	result = execute_flux_query(flux_query)
	return result