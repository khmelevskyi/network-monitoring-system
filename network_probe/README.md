# network-monitoring-system
The network monitoring system

## Initial Set Up
Make sure to enable SSH communication.

Execute:
```. ./network_probe/network_manager_setup.sh```
This will set up a Wi-Fi Access Point so that the Raspberry PI 4 can act as a router

Do:
```cp network_probe/.env.example network_probe/.env```
Edit the file network_probe/.env inputting the configurations

Launch everything with:
```sudo docker compose up --build -d```


## Suricata
### General
Main sections in the suricata.yaml:
- af-packet
- default-rule-path
- rule-files

### Testing
Do:
- ```curl http://testmynids.org/uid/index.html```

Now verify the central server to check if you received an alert about Bad Traffic

