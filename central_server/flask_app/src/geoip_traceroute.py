import subprocess
import requests
import json
import ipaddress

from src.influxdb_funcs import flux_get_flows

# Set the IPInfo API endpoint
IPINFO_URL = "http://ipinfo.io/{}/json"

# Function to check if an IP is private (local)
def is_private_ip(ip):
    return ipaddress.ip_address(ip).is_private

def enrich_flows():
    result = flux_get_flows()
    total_json_data = []
    
    for table in result:
        for record in table.records:
            public_ip = record["_value"]

            if is_private_ip(public_ip):
                continue

            # Fetch GeoIP & Hostname data from ipinfo.io
            try:
                response = requests.get(IPINFO_URL.format(public_ip), timeout=5)
                data = response.json()

                country = data.get("country", "Unknown")
                city = data.get("city", "Unknown")
                region = data.get("region", "Unknown")
                loc = data.get("loc", "Unknown")  # Latitude, Longitude
                org = data.get("org", "Unknown")
                hostname = data.get("hostname", "Unknown")
                timezone = data.get("timezone", "Unknown")
                postal = data.get("postal", "Unknown")

            except requests.RequestException:
                country = city = region = loc = org = hostname = timezone = postal = "Unknown"

            # Run Traceroute (MTR)
            # traceroute_cmd = f"mtr -r -n {public_ip}"
            # traceroute_result = subprocess.run(traceroute_cmd.split(), capture_output=True, text=True).stdout

            # Format the InfluxDB line
            # influx_line = (
            #     f'geoip,ip={public_ip} country="{country}",city="{city}",region="{region}",loc="{loc}",'
            #     f'org="{org}",hostname="{hostname}",timezone="{timezone}",postal="{postal}"\n'
            #     f'traceroute,ip={public_ip} path="{traceroute_result.strip()}"'
            # )
            influx_line = (
                f'geoip,ip={public_ip} country="{country}",city="{city}",region="{region}",loc="{loc}",'
                f'org="{org}",hostname="{hostname}",timezone="{timezone}",postal="{postal}"\n'
                f'traceroute,ip={public_ip}'
            )

            # Format JSON response
            json_data = {
                "ip": public_ip,
                "country": country,
                "city": city,
                "region": region,
                "location": loc,
                "organization": org,
                "hostname": hostname,
                "timezone": timezone,
                "postal": postal,
                # "traceroute": traceroute_result.strip().split("\n"),
            }

            # Print results (for testing)
            # print("\n--- InfluxDB Line Protocol ---")
            # print(influx_line)
            # print("\n--- JSON Response ---")
            # print(json.dumps(json_data, indent=4))
            total_json_data.append(json_data)

            # Store enriched data in InfluxDB (uncomment when ready)
            # write_api.write(bucket=BUCKET, org=ORG, record=influx_line)

    return json.dumps(total_json_data, indent=4)


