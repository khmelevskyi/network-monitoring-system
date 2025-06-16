# network-monitoring-system
The network monitoring system

## Prerequisitues
Install Docker Engine and Docker Compose Plugin
for Raspberry Pi 4 on Raspbian OS Bookworm 64:
https://docs.docker.com/engine/install/debian/

for Ubuntu 24.04.1:
https://docs.docker.com/engine/install/ubuntu/

Execute:
```. ./central_server/setup_static_ip.sh```
This will set up a computer to have the static IP.

Check the installation:
```sudo docker run hello-world```
```sudo docker compose version```

## Initial Set Up
Initially, go to the folder /repos/network-monitoring-system/central_server/secrets/
Inside this folder create two files:
```postgres-password.txt``` - with the password to your PostgresDB
```influxdb-admin-token.txt``` - with the admin token to your InfluxDB

Then do:
```cp central_server/.env.example central_server/.env```
Edit the central_server/.env file inputing your configurations

After that, launch everything with:
```sudo docker compose up --build -d```

and enter 127.0.0.1:5000/admin webpage in order to set up your first and main admin

*NOTE* if running locally, also do:
```flask --app src.app:create_app db upgrade```
This will create the necessary tables on your Postgres DB


## Adding Routers (Network Probes) To The Central Server
First, make sure SSH communication is enabled on network probe's side.
```ssh-keygen -t rsa -b 2048``` - generate the ssh key for a computer
```ssh-copy-id -i .ssh/id_rsa.pub <target_user>@<target_ip>``` - copy the public ssh key to the network probe
```ssh -i .ssh/id_rsa <target_user>@<target_ip>``` - verify if everything worked. You should be logged into the network probe's terminal


## Flask Models to Postgres DB Migrations
Initial setup of migrations
```cd repos/network-monitoring-system/central_server/flask_app```
```flask --app src.app:create_app db init```
```flask --app src.app:create_app db migrate -m "Initial migration"```
```flask --app src.app:create_app db upgrade```

With new changes to the models repeat:
```flask --app src.app:create_app db migrate -m "Initial migration"```
```flask --app src.app:create_app db upgrade```


