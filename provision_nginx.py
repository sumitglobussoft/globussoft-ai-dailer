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

# First clear out the bad symlink to unbreak nginx tests
exec_sudo("rm -f /etc/nginx/sites-enabled/demo-callified-ai")

# 5. Setup Nginx properly
exec_cmd("cat << 'EOF' > /tmp/demo-nginx\n" + raw_nginx + "\nEOF")
exec_sudo("mv /tmp/demo-nginx /etc/nginx/sites-available/demo-callified-ai")
exec_sudo("ln -sf /etc/nginx/sites-available/demo-callified-ai /etc/nginx/sites-enabled/")
exec_sudo("systemctl restart nginx")

# 6. Certbot
exec_sudo("certbot --nginx -d demo.callified.ai --non-interactive --agree-tos -m dev@globussoft.com --redirect")

print("Provisioning NGINX complete!")
ssh.close()
