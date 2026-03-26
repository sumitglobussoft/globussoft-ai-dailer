import paramiko
import os
import re

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
with open(env_path) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

HOSTNAME = os.environ.get("DEPLOY_HOST", "163.227.174.141")
USERNAME = os.environ.get("DEPLOY_USER", "empcloud-development")
PASSWORD = os.environ.get("DEPLOY_PASS")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD)

def exec_sudo(cmd):
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S {cmd}")
    stdin.write(PASSWORD + '\n')
    stdin.flush()
    return stdout.read().decode(), stderr.read().decode()

out, err = exec_sudo("cat /etc/mysql/debian.cnf")
match = re.search(r"password = (.*)", out)
if match:
    db_pass = match.group(1).strip()
    
    # Check tables in original
    out1, err1 = exec_sudo(f"mysql -u debian-sys-maint -p'{db_pass}' -e 'SHOW TABLES IN callified_ai;'")
    print("Callified AI tables:", out1)
    
    # Check tables in demo
    out2, err2 = exec_sudo(f"mysql -u debian-sys-maint -p'{db_pass}' -e 'SHOW TABLES IN demo_callified_ai;'")
    print("Demo AI tables:", out2)

    exec_sudo("ls -la /tmp/dump.sql")
ssh.close()
