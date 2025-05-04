from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from sqlalchemy.exc import IntegrityError

from src.config import (INFLUXDB_HOST, INFLUXDB_PORT,
    INFLUXDB_ORG, INFLUXDB_TOKEN, INFLUXDB_BUCKET)


INFLUXDB_URL = f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}"


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


def execute_flux_query(query):
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        tables = client.query_api().query(query)
        return tables


def flux_update_routers():
    flux_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "arp_entry")
        |> keep(columns: ["rpi_mac", "rpi_description", "rpi_public_ip", "rpi_local_ip", "rpi_ssh_username", "_time"])
        |> last(column: "_time")
    '''

    result = execute_flux_query(flux_query)
    return result


def flux_update_devices():
    # Flux query
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


def flux_get_data_for_ip_entropy_check():
    flux_query = f'''
        from(bucket: "network-data")
          |> range(start: -15m)
          |> filter(fn: (r) => r._measurement == "netflow")
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> filter(fn: (r) => contains(value: r.src, set: ["192.168.4.1", "192.168.4.84", "192.168.4.27"])) // Filter by your list of src IPs
          |> group(columns: ["src", "dst"])
          |> sum(column: "in_bytes")  // total per (src, dst)
          |> group(columns: ["src"])  // regroup by src for entropy
    '''

    result = execute_flux_query(flux_query)
    return result


def flux_get_data_for_botnet_activity_check():
    flux_query = '''
        import "date"
        from(bucket: "network-data")
            |> range(start: -30m)
            |> filter(fn: (r) => r._measurement == "netflow")
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> filter(fn: (r) => contains(value: r.src, set: ["192.168.4.1", "192.168.4.84", "192.168.4.27"])) // Filter by your list of src IPs
            |> map(fn: (r) => ({ r with _time: date.truncate(t: r._time, unit: 1s)}))
            |> keep(columns: ["_time", "src", "dst"])
            |> group(columns: ["_time", "src", "dst"])
            |> last(column: "_time")
            |> sort(columns: ["src", "dst", "_time"])
    '''

    result = execute_flux_query(flux_query)
    return result


def flux_get_recent_flows(device_ip, start_time, end_time):
    ip_list = [ip.strip() for ip in device_ip.strip('{}').split(',')]
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