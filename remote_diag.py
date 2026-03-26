import paramiko

host = "163.227.174.141"
username = "empcloud-development"
password = "rSPa3izkYPtAjCFLa5cqPDpsFvV071KN9u"

print("Authenticating with EC2 Dropet via correct ENV password...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=username, password=password, timeout=10)

print("Connected. Deploying Git Pull and restarting systemd...")
command1 = f"cd ~/callified-ai && git pull origin main && echo '{password}' | sudo -S systemctl restart gpt-callified-ai.service 2>&1"
stdin, stdout, stderr = client.exec_command(command1)
print(stdout.read().decode().strip())

print("Pulling latest server logs for exotel...")
command2 = "grep -iE 'recording' /home/empcloud-development/callified-ai/logs/uvicorn.error.log | tail -n 100"
stdin2, stdout2, stderr2 = client.exec_command(command2)
print("--- LATEST SERVER LOGS ---")
print(stdout2.read().decode().strip())
print(stdout2.read().decode().strip())

client.close()
