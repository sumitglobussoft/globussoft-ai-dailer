"""
deploy.py — Deploy Callified AI to the test server via SSH.

Pulls latest code, rebuilds the frontend, and restarts the backend service.
Requires: pip install paramiko, and a .env file with DEPLOY_HOST/USER/PASS.
"""

import os
import sys
import time

try:
    import paramiko
except ImportError:
    print("ERROR: paramiko not installed. Run: pip install paramiko")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("DEPLOY_HOST", "163.227.174.141")
USER = os.getenv("DEPLOY_USER", "empcloud-development")
PASS = os.getenv("DEPLOY_PASS")

if not PASS:
    print("ERROR: DEPLOY_PASS not set in .env")
    sys.exit(1)

REMOTE_DIR = "~/callified-ai"
SERVICE_NAME = "callified-ai.service"


def ssh_exec(ssh, cmd, label=None, sudo=False):
    """Execute a command over SSH and print output."""
    if sudo:
        cmd = f"echo {PASS} | sudo -S {cmd}"
    if label:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    if err and "[sudo]" not in err and "Warning" not in err:
        print(f"STDERR: {err}")
    return out


def deploy():
    print(f"Connecting to {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    print("Connected.\n")

    # 1. Pull latest code
    ssh_exec(ssh, f"cd {REMOTE_DIR} && git pull origin main 2>&1", "Pulling latest code")

    # 2. Build frontend on server
    ssh_exec(ssh, f"cd {REMOTE_DIR}/frontend && npm install --production=false 2>&1 | tail -3", "Installing frontend deps")
    ssh_exec(ssh, f"cd {REMOTE_DIR}/frontend && npm run build 2>&1", "Building frontend")

    # 3. Install backend deps if requirements changed
    ssh_exec(ssh, f"cd {REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt -q 2>&1 | tail -5", "Updating backend deps")

    # 4. Verify the service is running, then restart
    ssh_exec(ssh, f"systemctl is-active {SERVICE_NAME} 2>&1", "Checking service status")
    ssh_exec(ssh, f"systemctl restart {SERVICE_NAME} 2>&1", "Restarting backend service", sudo=True)
    time.sleep(3)
    ssh_exec(ssh, f"systemctl is-active {SERVICE_NAME} 2>&1", "Verifying service restarted")

    # 5. Health check
    ssh_exec(ssh, "curl -sf http://localhost:8001/api/debug/health 2>&1 || echo 'Health check failed'", "Health check")

    # 6. Verify frontend loads
    ssh_exec(ssh, "curl -sI http://localhost:8001/assets/index-ht7JoN8I.js 2>&1 | head -3", "Verifying frontend assets")

    ssh.close()
    print(f"\n{'='*60}")
    print("  Deployment complete!")
    print(f"  Site: https://test.callified.ai")
    print(f"{'='*60}")


if __name__ == "__main__":
    deploy()
