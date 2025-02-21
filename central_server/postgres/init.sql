-- Create database
CREATE DATABASE network_monitor_central;

-- Connect to the new database
\c network_monitor_central

-- Create user
CREATE USER user_network_monitor WITH PASSWORD '${DB_USER_PASSWORD}';

-- Grant permissions
GRANT CONNECT ON DATABASE network_monitor_central TO user_network_monitor;
GRANT USAGE, CREATE ON SCHEMA public TO user_network_monitor;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO user_network_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO user_network_monitor;

