import paramiko
import os
import re
import time

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
    
    print("Dumping...")
    # using sh -c so the redirect evaluates under root
    cmd1 = f"sh -c 'mysqldump -u debian-sys-maint -p\"{db_pass}\" callified_ai > /tmp/dump2.sql'"
    out1, err1 = exec_sudo(cmd1)
    print("DUMP:", out1, err1)
    
    print("Restoring...")
    cmd2 = f"sh -c 'mysql -u debian-sys-maint -p\"{db_pass}\" demo_callified_ai < /tmp/dump2.sql'"
    out2, err2 = exec_sudo(cmd2)
    print("RESTORE:", out2, err2)
    
    # Check tables again
    out3, err3 = exec_sudo(f"mysql -u debian-sys-maint -p\"{db_pass}\" -e 'SHOW TABLES IN demo_callified_ai;'")
    print("Demo Tables now:", out3)

    exec_sudo("systemctl restart demo-callified-ai.service")
    time.sleep(2)
    out4, err4 = exec_sudo("systemctl status demo-callified-ai.service --no-pager")
    print("Service Status:", out4)

ssh.close()
