import paramiko

from src.config import SSH_HOST, SSH_USER, SSH_KEY_PATH

def execute_ssh_command(command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    ssh.close()

    return output

def block_device(mac):
    command = f"sudo iptables -A INPUT -m mac --mac-source {mac} -j DROP"
    return execute_ssh_command(command)

def unblock_device(mac):
    command = f"sudo iptables -D INPUT -m mac --mac-source {mac} -j DROP"
    return execute_ssh_command(command)
