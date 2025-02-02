# network-monitoring-system
The network monitoring system

## Central Server
### Init database
```python3 -c "from database import init_db; init_db()"```

## Suricata
### Installation
- ```sudo apt update```
- ```sudo apt install suricata jq```
- ```sudo suricata-update```
	- installs Suricata Signatures/Rules which fetches the ET Open ruleset and the rules are saved under /var/lib/suricata/rules/suricata.rules
- update /etc/suricata/suricata.yaml
- update /etc/suricata/rules/custom.rules
- ```sudo suricata -T -c /etc/suricata/suricata.yaml```
- ```sudo systemctl enable suricata```
- ```sudo systemctl restart suricata```

Main sections in the etc/suricata/suricata.yaml:
- af-packet
- default-rule-path
- rule-files

### Testing
- add alert to /etc/suricata/rules/custom.rules
	- the alert is ```alert ip any any -> any any (msg:"GPL ATTACK_RESPONSE id check returned root"; content:"uid=0|28|root|29|"; classtype:bad-unknown; sid:2100498; rev:7; metadata:created_at 2010_09_23, updated_at 2010_09_23;)```
- ```sudo systemctl restart suricata```
- ```sudo tail -f /var/log/suricata/fast.log```
- ```curl http://testmynids.org/uid/index.html```
- the following output should now be seen in the log:
	- ```[1:2100498:7] GPL ATTACK_RESPONSE id check returned root [**] [Classification: Potentially Bad Traffic] [Priority: 2] {TCP} 217.160.0.187:80 -> 10.0.0.23:41618```


