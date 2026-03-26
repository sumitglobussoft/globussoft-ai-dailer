import paramiko
import os
import time
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
    
    print("Creating database and granting privileges...")
    out2, err2 = exec_sudo(f"mysql -u debian-sys-maint -p{db_pass} -e \"CREATE DATABASE IF NOT EXISTS demo_callified_ai; GRANT ALL PRIVILEGES ON demo_callified_ai.* TO 'callified'@'localhost'; FLUSH PRIVILEGES;\"")
    print(out2, err2)
    
    print("Dumping callified_ai...")
    exec_sudo(f"mysqldump -u debian-sys-maint -p{db_pass} callified_ai > /tmp/dump.sql")
    
    print("Restoring to demo_callified_ai...")
    exec_sudo(f"mysql -u debian-sys-maint -p{db_pass} demo_callified_ai < /tmp/dump.sql")
    
    print("Restarting service...")
    exec_sudo("systemctl restart demo-callified-ai.service")
    time.sleep(2)
    out3, err3 = exec_sudo("systemctl status demo-callified-ai.service --no-pager")
    print(out3)
else:
    print("No debian.cnf password found")
ssh.close()
