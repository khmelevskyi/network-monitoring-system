import os
from dotenv import load_dotenv

load_dotenv()


def get_config(key, default=None, is_secret_file=False, prefix_for_file_path=""):
    """
    Retrieves configuration values, handling secret files and local prefixes.
    """
    value = os.getenv(key, default)
    if is_secret_file and value:
        try:
            with open(prefix_for_file_path + value, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Secret file not found: {value}")
            return default
        except IOError:
            print(f"Warning: Could not read secret file: {value}")
            return default
    return value


# Load environment variables using the new function
INFLUXDB_HOST = get_config("FLASK_INFLUXDB_HOST", "influxdb")
INFLUXDB_PORT = 8086
INFLUXDB_ORG = get_config("DOCKER_INFLUXDB_INIT_ORG", "network-monitoring")
INFLUXDB_BUCKET = get_config("DOCKER_INFLUXDB_INIT_BUCKET", "network-data")
INFLUXDB_TOKEN = get_config("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN_FILE", "", is_secret_file=True)

POSTGRES_HOST = get_config("FLASK_POSTGRES_HOST", "postgres")
POSTGRES_PORT = 5432
POSTGRES_DB = get_config("POSTGRES_DB", "network_monitor_central")
POSTGRES_USER = get_config("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = get_config("POSTGRES_PASSWORD_FILE", "", is_secret_file=True)

IPINFO_TOKEN = get_config("IPINFO_TOKEN", "")

SSH_PRIVATE_KEY_PATH = os.getenv("SSH_PRIVATE_KEY_DOCKER_PATH")

FLASK_RUN_MODE_IF_DOCKER = get_config("FLASK_RUN_MODE_IF_DOCKER", "true")

if FLASK_RUN_MODE_IF_DOCKER == "false":
    SSH_PRIVATE_KEY_PATH = get_config("SSH_PRIVATE_KEY_LOCAL_PATH")
    INFLUXDB_HOST = "localhost"
    INFLUXDB_PORT = get_config("INFLUXDB_BIND_PORT", 8086)
    INFLUXDB_TOKEN = get_config("INFLUXDB_TOKEN_LOCAL_FILE", "", is_secret_file=True, prefix_for_file_path=".")
    POSTGRES_HOST = "localhost"
    POSTGRES_PORT = get_config("POSTGRES_BIND_PORT", 5432)
    POSTGRES_PASSWORD = get_config("POSTGRES_PASSWORD_LOCAL_FILE", "", is_secret_file=True, prefix_for_file_path=".")

SECRET_KEY = get_config("SECRET_KEY", "supersecretkey")
