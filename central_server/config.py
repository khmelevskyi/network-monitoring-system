import os

from dotenv import load_dotenv


load_dotenv()

# Load environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 5433)
DB_NAME = os.getenv("DB_NAME", "network_monitor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # For session security
SSH_HOST = os.getenv("SSH_HOST", "raspberrypi.local")
SSH_USER = os.getenv("SSH_USER", "pi")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa")
