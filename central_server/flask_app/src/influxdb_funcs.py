from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_ORG, INFLUXDB_TOKEN
from src.models import db, Router, Device


def update_devices():
    # InfluxDB connection
    print(INFLUXDB_TOKEN)
    print(INFLUXDB_ORG)
    client = InfluxDBClient(
        url="http://localhost:8086",
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )

    query_api = client.query_api()

    # Flux query
    flux_query = '''
    from(bucket: "network-data")
      |> range(start: -30m)
      |> filter(fn: (r) => r._measurement == "arp_entry")
      |> group(columns: ["rpi_mac", "_value", "ip"])
      |> last()
    '''

    # Execute query
    result = query_api.query(flux_query)
    print(result)

    # Process results
    for table in result:
        for record in table.records:
            rpi_mac = record.values.get("rpi_mac")
            device_mac = record.values.get("_value")
            ip_address = record.values.get("ip")

            # Find the router
            router = Router.query.filter_by(mac_address=rpi_mac).first()
            if router:
                # Check if device exists
                device = Device.query.filter_by(mac_address=device_mac, router_id=router.id).first()
                if device:
                    # Update existing device
                    if device.local_ip_address != ip_address:
                        device.local_ip_address = ip_address
                        db.session.add(device)
                else:
                    # Add new device
                    new_device = Device(
                        mac_address=device_mac,
                        local_ip_address=ip_address,
                        router_id=router.id
                    )
                    db.session.add(new_device)

                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    print(f"Error updating device {device_mac} for router {rpi_mac}")

    # Update last_updated_data for all routers
    Router.query.update({Router.last_updated_data: datetime.utcnow()})
    db.session.commit()

    # Close the client
    client.close()
