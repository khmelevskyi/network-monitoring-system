import os

from dotenv import load_dotenv


load_dotenv()

def read_secret(secret_name, default_value=""):
    secret_file_path = os.environ.get(f'{secret_name}_FILE')
    if not secret_file_path:
        return default_value
    try:
        with open(secret_file_path, 'r') as secret_file:
            return secret_file.read().strip()
    except FileNotFoundError:
        return default_value
    except IOError:
        print(f"Warning: Could not read secret file for {secret_name}")
        return default_value

# Load environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_DB = os.getenv("POSTGRES_DB", "network_monitor_central")
POSTGRES_USER = read_secret("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = read_secret("POSTGRES_PASSWORD", "")

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST", "localhost")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT", 8086)
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "network_monitoring")
INFLUXDB_TOKEN = read_secret("INFLUXDB_TOKEN", "")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # For session security
