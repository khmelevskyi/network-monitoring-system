import json
import ipaddress
# import subprocess

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
    result = flux_get_unique_ip_addresses(ip_address)
    enriched_ips_data = []

    for table in result:
        for record in table.records:
            public_ip = record["_value"]

            if is_private_ip(public_ip):
                continue

            # Fetch GeoIP & Hostname data from ipinfo.io
            try:
                response = requests.get(IPINFO_URL.format(public_ip, IPINFO_TOKEN), timeout=5)
                data = response.json()

                print(data)

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
                    "postal": postal
                })

            except requests.RequestException:
                print(f"Error fetching data for IP: {public_ip}")

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
                    "postal": stmt.excluded.postal
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

    #### /


            # Run Traceroute (MTR)
            # traceroute_cmd = f"mtr -r -n {public_ip}"
            # traceroute_result = subprocess.run(traceroute_cmd.split(), capture_output=True, text=True).stdout

            # Format the InfluxDB line
            # influx_line = (
            #     f'geoip,ip={public_ip} country="{country}",city="{city}",region="{region}",loc="{loc}",'
            #     f'org="{org}",hostname="{hostname}",timezone="{timezone}",postal="{postal}"\n'
            #     f'traceroute,ip={public_ip} path="{traceroute_result.strip()}"'
            # )

            # influx_line = (
            #     f'geoip,ip={public_ip} country="{country}",city="{city}",region="{region}",'
            #     f'latitude="{latitude}",longitude="{longitude}"'
            #     f'org="{org}",hostname="{hostname}",timezone="{timezone}",postal="{postal}"'
            # )

            # Format JSON response
            # json_data = {
            #     "ip": public_ip,
            #     "country": country,
            #     "city": city,
            #     "region": region,
            #     "latitude": latitude,
            #     "longitude": longitude,
            #     "organization": org,
            #     "hostname": hostname,
            #     "timezone": timezone,
            #     "postal": postal,
            #     # "traceroute": traceroute_result.strip().split("\n"),
            # }

            # Print results (for testing)
            # print("\n--- InfluxDB Line Protocol ---")
            # print(influx_line)
            # print("\n--- JSON Response ---")
            # print(json.dumps(json_data, indent=4))
            
            # total_json_data.append(json_data)

            # Store enriched data in InfluxDB (uncomment when ready)
            # write_api.write(bucket=BUCKET, org=ORG, record=influx_line)

    # return json.dumps(total_json_data, indent=4)


