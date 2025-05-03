from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_ORG, INFLUXDB_TOKEN, INFLUXDB_BUCKET


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
    # Flux query
    flux_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "arp_entry")
        |> keep(columns: ["rpi_mac", "rpi_description", "rpi_public_ip", "rpi_local_ip", "rpi_ssh_username", "_time"])
        |> last(column: "_time")
    '''

    # Execute query
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

    # Execute query
    result = execute_flux_query(flux_query)

    return result


def flux_get_unique_ip_addresses(ip_address):
    if not ip_address:
        flux_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -15m)
                |> filter(fn: (r) => r["_measurement"] == "netflow")
                |> filter(fn: (r) => r["_field"] == "src" or r["_field"] == "dst")
                |> keep(columns: ["_value"])
                |> distinct(column: "_value")
            '''

    elif ip_address:
        flux_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -15m)
                |> filter(fn: (r) => r["_measurement"] == "netflow")
                |> filter(fn: (r) => r["_field"] == "src" or r["_field"] == "dst")
                |> filter(fn: (r) => r["_value"] == "{ip_address}")
                |> keep(columns: ["_value"])
                |> distinct(column: "_value")
            '''

    result = execute_flux_query(flux_query)
    return result


def flux_get_data_for_port_scanning_detection():
    flux_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "netflow")
        |> filter(fn: (r) => r._field == "in_packets" or r._field == "src"  or r._field == "dst_port")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> filter(fn: (r) => not r.src =~ /^192\.168\.4\..*/ and not r.src =~ /::/)
        |> group(columns: ["src", "dst_port"])
        |> sum(column: "in_packets")
    '''

    # result = execute_flux_query(flux_query)
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        result = client.query_api().query(flux_query)
    return result