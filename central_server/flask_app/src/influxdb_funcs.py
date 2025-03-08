from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_ORG, INFLUXDB_TOKEN
from src.models import db, Router, Device


INFLUXDB_URL = f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}"
INFLUXDB_BUCKET = "network-data"


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


def batch_query_flux_last_seen(ip_addresses):
    if not ip_addresses:
        return {}

    ip_filter = " or ".join([f'r.src == "{ip}" or r.dst == "{ip}"' for ip in ip_addresses])

    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -30d)
    |> filter(fn: (r) => r["_measurement"] == "netflow")
    |> filter(fn: (r) => {ip_filter})
    |> last(column: "_time")
    |> keep(columns: ["_time", "src", "dst"])
    """
    
    print(query)
    tables = execute_flux_query(query)
    last_seen_map = {}

    for table in tables:
        for record in table.records:
            ip = record.values.get("src") or record.values.get("dst")
            last_seen_map[ip] = record.values.get("_time")

    print(last_seen_map)
    return last_seen_map



def batch_query_flux_flows(ip_addresses):
    if not ip_addresses:
        return {}

    ip_filter = " or ".join([f'r.src == "{ip}" or r.dst == "{ip}"' for ip in ip_addresses])

    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "netflow")
    |> filter(fn: (r) => {ip_filter})
    |> filter(fn: (r) => r["_field"] == "in_bytes")
    |> count(column: "_value")
    """
    
    print(query)
    tables = execute_flux_query(query)
    flows_map = {ip: {"1h": 0, "30d": 0} for ip in ip_addresses}

    for table in tables:
        for record in table.records:
            ip = record.values.get("src") or record.values.get("dst")
            if ip in flows_map.keys():
                flows_map[ip]["1h"] = record.values.get("_value", 0)

    # Query for 30-day avg
    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -30d)
    |> filter(fn: (r) => r["_measurement"] == "netflow")
    |> filter(fn: (r) => {ip_filter})
    |> filter(fn: (r) => r["_field"] == "in_bytes")
    |> aggregateWindow(every: 1h, fn: count, column: "_value", createEmpty: false)
    |> mean(column: "_value")
    """
    
    tables = execute_flux_query(query)
    for table in tables:
        for record in table.records:
            ip = record.values.get("src") or record.values.get("dst")
            if ip in flows_map.keys():
                flows_map[ip]["30d"] = record.values.get("_value", 0)

    print(flows_map)
    return flows_map



def batch_query_flux_traffic(ip_addresses):
    if not ip_addresses:
        return {}

    ip_filter = " or ".join([f'r.src == "{ip}" or r.dst == "{ip}"' for ip in ip_addresses])

    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "netflow")
    |> filter(fn: (r) => {ip_filter})
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    """

    # Query for 1-hour mean
    query_1h = query + '|> mean(column: "in_bytes")'
    
    # Query for 30-day avg
    query_30d = query + """
    |> aggregateWindow(every: 1h, fn: mean, column: "in_bytes", createEmpty: false)
    |> mean(column: "in_bytes")
    """

    traffic_map = {ip: {} for ip in ip_addresses}

    for time_range, query in [("1h", query_1h), ("30d", query_30d)]:
        tables = execute_flux_query(query)
        for table in tables:
            for record in table.records:
                ip = record.values.get("src") or record.values.get("dst")
                if ip in traffic_map.keys():
                    if record.values.get("src"):
                        in_bytes = record.values.get("in_bytes", 0)
                        traffic_map[ip][f"outgoing_{time_range}"] = convert_bytes(in_bytes)  # Assuming symmetrical traffic
                    elif record.values.get("dst"):
                        in_bytes = record.values.get("in_bytes", 0)
                        traffic_map[ip][f"incoming_{time_range}"] = convert_bytes(in_bytes)

    return traffic_map




def update_routers():
    # InfluxDB connection
    client = InfluxDBClient(
        url=f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}",
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )

    query_api = client.query_api()

    # Flux query
    flux_query = '''
    from(bucket: "network-data")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "netflow")
        |> keep(columns: ["rpi_mac", "rpi_description", "rpi_public_ip", "rpi_local_ip", "rpi_ssh_username", "_time"])
        |> last(column: "_time")
    '''

    # Execute query
    result = query_api.query(flux_query)

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
                # Add new device
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

    # Close the client
    client.close()


def update_devices():
    # InfluxDB connection
    client = InfluxDBClient(
        url=f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}",
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )

    query_api = client.query_api()

    # Flux query
    flux_query = '''
    from(bucket: "network-data")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "arp_entry" and r.iface == "wlan0")
        |> keep(columns: ["_time", "_field", "_value", "mac", "rpi_mac"])
        |> last(column: "_time")
    '''

    # Execute query
    result = query_api.query(flux_query)

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

    # Close the client
    client.close()
