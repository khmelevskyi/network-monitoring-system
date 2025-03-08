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


def update_routers():
    # Flux query
    flux_query = '''
    from(bucket: "network-data")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "netflow")
        |> keep(columns: ["rpi_mac", "rpi_description", "rpi_public_ip", "rpi_local_ip", "rpi_ssh_username", "_time"])
        |> last(column: "_time")
    '''

    # Execute query
    result = execute_flux_query(flux_query)

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


def update_devices():
    # Flux query
    flux_query = '''
    from(bucket: "network-data")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "arp_entry" and r.iface == "wlan0")
        |> keep(columns: ["_time", "_field", "_value", "mac", "rpi_mac"])
        |> last(column: "_time")
    '''

    # Execute query
    result = execute_flux_query(flux_query)

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

