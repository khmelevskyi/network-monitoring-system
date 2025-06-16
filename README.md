# Portable Network Anomaly Detection System

This project is a **portable system for detecting anomalous network behavior** in local networks, built using a Raspberry Pi 4 and a centralized server. It is designed to detect and alert on suspicious activity such as botnet communications, data exfiltration attempts, and connections to blacklisted IP addresses.

The system is composed of two main components:

---

## 📡 `network_probe/` — Network Probe on Raspberry Pi

This directory contains all the code and configuration for the **Raspberry Pi 4**, which acts as a Wi-Fi access point and network firewall. It is responsible for:

- Capturing and analyzing local network traffic
- Running Suricata for intrusion detection
- Exporting flow data via Softflowd
- Forwarding all relevant metrics and alerts to the central server
- Executing firewall-level blocking of suspicious devices when requested

📄 See [`network_probe/README.md`](./network_probe/README.md) for full details.

---

## 🧠 `central_server/` — Central Monitoring & Control Server

This directory contains the **central server** component, typically running on a VM or a laptop. It includes:

- A Flask-based web application with user authentication
- A PostgreSQL database for storing devices, routers, alerts, and more
- InfluxDB for storing time-series data and anomaly detection input
- Grafana dashboards for visualizing network activity and alerts
- Logic for custom anomaly detection (e.g., entropy-based exfiltration, botnet patterns)
- APIs and logic for triggering traffic blocking on the Raspberry Pi

📄 See [`central_server/README.md`](./central_server/README.md) for full details.

---

## 🧪 Use Case and Demo

The system is intended for demonstration purposes (e.g. as part of a diploma project) and is capable of:

- Monitoring and detecting threats in real-time
- Providing interactive dashboards and logs for security analysts
- Blocking or ignoring specific IPs based on white/blacklists
- Running custom anomaly detection logic alongside Suricata

---

## 🧰 Technologies Used

- **Flask**, **PostgreSQL** — Central web backend and database
- **Suricata**, **Softflowd**, **iptables** — Traffic analysis and firewall on Raspberry Pi
- **Telegraf**, **InfluxDB**, **Grafana** — Data collection, storage, and visualization
- **Docker**, **Docker Compose** — Containerized deployment for both components

---

## 🚀 Getting Started

To deploy or run this project, navigate to either subdirectory and follow its respective setup instructions:

- [`network_probe/README.md`](./network_probe/README.md)
- [`central_server/README.md`](./central_server/README.md)

---
