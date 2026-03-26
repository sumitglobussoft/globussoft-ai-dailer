import paramiko
import os

# Read .env locally
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

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())

print("--- Viewing /home/empcloud-development/callified-ai/.env ---")
run("cat /home/empcloud-development/callified-ai/.env")

ssh.close()
