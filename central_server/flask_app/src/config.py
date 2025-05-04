import os

from dotenv import load_dotenv


load_dotenv()

def read_secret(secret_name, default_value=""):
    secret_file_path = os.environ.get(secret_name)
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
POSTGRES_HOST = os.getenv("FLASK_POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_DB = os.getenv("POSTGRES_DB", "network_monitor_central")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = read_secret("POSTGRES_PASSWORD_FILE", "")

INFLUXDB_HOST = os.getenv("FLASK_INFLUXDB_HOST", "localhost")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT", 8086)
INFLUXDB_ORG = os.getenv("DOCKER_INFLUXDB_INIT_ORG", "network_monitoring")
INFLUXDB_BUCKET = os.getenv("DOCKER_INFLUXDB_INIT_BUCKET", "network-data")
INFLUXDB_TOKEN = read_secret("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN_FILE", "")

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")

FLASK_RUN_MODE_IF_DOCKER = os.getenv("FLASK_RUN_MODE_IF_DOCKER", "true")
if FLASK_RUN_MODE_IF_DOCKER == "true":
    SSH_PRIVATE_KEY_PATH = os.getenv("SSH_PRIVATE_KEY_DOCKER_PATH")
elif FLASK_RUN_MODE_IF_DOCKER == "false":
    SSH_PRIVATE_KEY_PATH = os.getenv("SSH_PRIVATE_KEY_LOCAL_PATH")
    POSTGRES_PASSWORD = "." + read_secret("POSTGRES_PASSWORD_LOCAL_FILE", "")
    INFLUXDB_TOKEN = "." + read_secret("INFLUXDB_TOKEN_LOCAL_FILE", "")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # For session security
