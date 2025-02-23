import paramiko

def execute_ssh_command(command, instruction_msg, ip, username, ssh_key_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(ip, username, ssh_key_path)
        ssh.connect(ip, username=username, key_filename=ssh_key_path)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        print(output)
        ssh.close()
        return f"{instruction_msg} {mac} on {rpi_mac}"
    except Exception as e:
        return f"SSH Error: {str(e)}", 500


ip = "192.168.0.107"
command = "arp -e"
instruction_msg = "PP"
username = "eugene"
ssh_key_path = "/home/eugene/repos/network-monitoring-system/central_server/secrets/rpi_01_id_rsa"
result = execute_ssh_command(command, instruction_msg, ip, username, ssh_key_path)
print(result)
