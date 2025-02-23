# network-monitoring-system
The network monitoring system

## Prerequisitues
Install Docker Engine and Docker Compose Plugin
for Raspberry Pi 4 on Raspbian OS Bookworm 64:
```for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done```
```sudo apt-get update```
```sudo apt-get install ca-certificates curl```
```sudo install -m 0755 -d /etc/apt/keyrings```
```sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc```
```sudo chmod a+r /etc/apt/keyrings/docker.asc```
```echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null```
```sudo apt-get update```
```sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin```

for Ubuntu 22.04:
```for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done```
```sudo apt-get update```
```sudo apt-get install ca-certificates curl```
```sudo install -m 0755 -d /etc/apt/keyrings```
```sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc```
```sudo chmod a+r /etc/apt/keyrings/docker.asc```
```echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null```
```sudo apt-get update```
```sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin```

Check the installation:
```sudo docker run hello-world```
```sudo docker compose version```

## Initial Set Up
Initially, add credentials to your postgresql database inside /repos/network-monitoring-system/central_server/secrets/ folder:
postgres-password.txt
postgres-user.txt

If running locally, and not on Docker, then also do the following:
```cd repos/network-monitoring-system/central_server/flask_app```
```cp src/.env.example src/.env```
and modify the src/.env file by specifying the port, host and database name and do:
```source ./src/.env```

Initial setup of migrations
```cd repos/network-monitoring-system/central_server/flask_app```
```flask --app src.app:create_app db init```
```flask --app src.app:create_app db migrate -m "Initial migration"```
```flask --app src.app:create_app db upgrade```

With new changes to the models repeat:
```flask --app src.app:create_app db migrate -m "Initial migration"```
```flask --app src.app:create_app db upgrade```


