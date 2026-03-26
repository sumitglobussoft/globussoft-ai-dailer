import paramiko
import os
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
    print(f"Running sudo: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S {cmd}")
    stdin.write(PASSWORD + '\n')
    stdin.flush()
    stdout_str = stdout.read().decode()
    stderr_str = stderr.read().decode()
    if stdout_str: print("STDOUT:", stdout_str)
    if stderr_str: print("STDERR:", stderr_str)
    return stdout_str

def exec_cmd(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout_str = stdout.read().decode()
    stderr_str = stderr.read().decode()
    if stdout_str: print("STDOUT:", stdout_str)
    if stderr_str: print("STDERR:", stderr_str)
    return stdout_str

# 1. Clone directory
exec_cmd("rm -rf /home/empcloud-development/demo-callified-ai")
exec_cmd("cp -r /home/empcloud-development/callified-ai /home/empcloud-development/demo-callified-ai")

# 2. Update .env
exec_cmd("sed -i 's/MYSQL_DATABASE=callified_ai/MYSQL_DATABASE=demo_callified_ai/g' /home/empcloud-development/demo-callified-ai/.env")
exec_cmd("sed -i 's/PUBLIC_SERVER_URL=https:\/\/test.callified.ai/PUBLIC_SERVER_URL=https:\/\/demo.callified.ai/g' /home/empcloud-development/demo-callified-ai/.env")

# 3. Clone DB
exec_cmd('mysql -u callified -pCallified@2026 -e "DROP DATABASE IF EXISTS demo_callified_ai; CREATE DATABASE demo_callified_ai;"')
exec_cmd('mysqldump -u callified -pCallified@2026 callified_ai > /tmp/dump.sql')
exec_cmd('mysql -u callified -pCallified@2026 demo_callified_ai < /tmp/dump.sql')
exec_cmd('rm /tmp/dump.sql')

# 4. Setup Systemd Service
exec_sudo("cp /etc/systemd/system/callified-ai.service /etc/systemd/system/demo-callified-ai.service")
exec_sudo("sed -i 's/callified-ai/demo-callified-ai/g' /etc/systemd/system/demo-callified-ai.service")
exec_sudo("sed -i 's/8001/8002/g' /etc/systemd/system/demo-callified-ai.service")
exec_sudo("systemctl daemon-reload")
exec_sudo("systemctl enable demo-callified-ai.service")
exec_sudo("systemctl restart demo-callified-ai.service")

# 5. Setup Nginx
exec_sudo("cp /etc/nginx/sites-available/callified-ai /etc/nginx/sites-available/demo-callified-ai")
exec_sudo("sed -i 's/test.callified.ai/demo.callified.ai/g' /etc/nginx/sites-available/demo-callified-ai")
exec_sudo("sed -i 's/8001/8002/g' /etc/nginx/sites-available/demo-callified-ai")
# If there are hardcoded SSL cert paths for test.callified.ai, we should clear them out or let certbot overwrite. Let's just run certbot.
# Certbot usually adds specific blocks. It's safer to just overwrite the server block with a clean HTTP one and let certbot do the HTTPS.
raw_nginx = '''server {
    server_name demo.callified.ai;
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
'''
exec_sudo(f"echo '{raw_nginx}' > /tmp/demo-nginx && mv /tmp/demo-nginx /etc/nginx/sites-available/demo-callified-ai")
exec_sudo("ln -sf /etc/nginx/sites-available/demo-callified-ai /etc/nginx/sites-enabled/")
exec_sudo("systemctl restart nginx")

# 6. Certbot
exec_sudo("certbot --nginx -d demo.callified.ai --non-interactive --agree-tos -m dev@globussoft.com --redirect")

print("Provisioning complete!")
ssh.close()
