import paramiko

from src.config import SSH_PRIVATE_KEY_PATH
from src.models import db, User, Router, Device


def execute_ssh_command(command, instruction_msg, rpi_mac, device_mac, ip, username, ssh_key_path):
	try:
		print(ip, username, ssh_key_path)
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, key_filename=ssh_key_path)
		stdin, stdout, stderr = ssh.exec_command(command)
		output = stdout.read().decode()
		print(output)
		ssh.close()
		return f"{instruction_msg} {device_mac} on {rpi_mac}"
	except Exception as e:
		return f"SSH Error: {str(e)}", 500



def ssh_block_device(rpi_mac, device_mac=None, device_local_ip=None):
	router = Router.query.filter_by(mac_address=rpi_mac).first()
	if not router:
		flash("Router not found", "danger")
		return redirect(url_for("main.dashboard"))

	if device_mac:
		device = Device.query.filter_by(mac_address=device_mac).first()
	elif device_local_ip:
		device = Device.query.filter_by(local_ip_address=device_local_ip).last()

	if not device:
		flash("Device not found", "danger")
		return redirect(url_for("main.dashboard"))

	if device.if_blocked == True:
		flash("Device is already blocked", "warning")
		return redirect(url_for("main.dashboard"))

	ip = router.public_ip_address  # Using local IP for internal SSH access (demo purposes)
	username = router.ssh_username
	ssh_key_path = SSH_PRIVATE_KEY_PATH
	print(ssh_key_path)

	ssh_command = f"sudo iptables -A INPUT -m mac --mac-source {device_mac} -j DROP && sudo iptables -A FORWARD -m mac --mac-source {device_mac} -j DROP"
	# ssh_command = "arp -e"

	result = execute_ssh_command(ssh_command, "Blocked", rpi_mac, device_mac, ip, username, ssh_key_path)
	print(result)

	device.if_blocked = True
	db.session.commit()



def ssh_unblock_device(rpi_mac, device_mac):
	router = Router.query.filter_by(mac_address=rpi_mac).first()
	if not router:
		flash("Router not found", "danger")
		return redirect(url_for("main.dashboard"))

	device = Device.query.filter_by(mac_address=device_mac).first()
	if not device:
		flash("Device not found", "danger")
		return redirect(url_for("main.dashboard"))

	if device.if_blocked == False:
		flash("Device is already unblocked", "warning")
		return redirect(url_for("main.dashboard"))

	ip = router.public_ip_address  # Using local IP for internal SSH access (demo purposes)
	username = router.ssh_username
	ssh_key_path = SSH_PRIVATE_KEY_PATH

	ssh_command = f"sudo iptables -D INPUT -m mac --mac-source {device_mac} -j DROP && sudo iptables -D FORWARD -m mac --mac-source {device_mac} -j DROP"
	# ssh_command = "arp -e"

	result = execute_ssh_command(ssh_command, "Unblocked", rpi_mac, device_mac, ip, username, ssh_key_path)
	print(result)

	device.if_blocked = False
	db.session.commit()
