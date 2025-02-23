import paramiko

def execute_ssh_command(command, instruction_msg, rpi_mac, mac, ip, username, ssh_key_path):
    try:
        print(ip, username, ssh_key_path)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, key_filename=ssh_key_path)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        print(output)
        ssh.close()
        return f"{instruction_msg} {mac} on {rpi_mac}"
    except Exception as e:
        return f"SSH Error: {str(e)}", 500

