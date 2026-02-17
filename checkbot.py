import os
import socket
import paramiko
from datetime import datetime
from dotenv import load_dotenv
import zulip
from pathlib import Path


# .env

env_path = Path(__file__).parent / ".env"

if load_dotenv(dotenv_path=env_path):
    print(f"✅ Loaded env from {env_path}")
else:
    print(f"❌ Failed to load {env_path}")
    exit(1)


#  required variables

required = ["ZULIP_EMAIL", "ZULIP_API_KEY", "ZULIP_SITE", "STREAM", "TOPIC", "SERVER_IP", "SSH_USER", "SSH_PASSWORD"]
missing = [v for v in required if not os.getenv(v)]

if missing:
    print(f"❌ Missing in .env: {', '.join(missing)}")
    exit(1)

client = zulip.Client(
    email=os.getenv("ZULIP_EMAIL"),
    api_key=os.getenv("ZULIP_API_KEY"),
    site=os.getenv("ZULIP_SITE")
)

STREAM       = os.getenv("STREAM")
TOPIC        = os.getenv("TOPIC")
SERVER_IP    = os.getenv("SERVER_IP")
SSH_USER     = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
SSH_PORT     = int(os.getenv("SSH_PORT", 22))


# funktions

def send_message(content):
    request = {
        "type": "stream",
        "to": STREAM,
        "topic": TOPIC,
        "content": content
    }
    result = client.send_message(request)
    if result.get("result") == "success":
        print(f"✅ Sent: {content}")
    else:
        print(f"❌ Send failed: {result}")

def check_ssh(host, port=22, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, OSError, ConnectionRefusedError):
        return False

def get_vm_hostname(ip, user, password, port=22, timeout=6):
    """
    Подключается по SSH и выполняет команду 'hostname'
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(
            hostname=ip,
            port=port,
            username=user,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False
        )
        
        stdin, stdout, stderr = ssh.exec_command("hostname")
        hostname = stdout.read().decode("utf-8").strip()
        
        error = stderr.read().decode("utf-8").strip()
        if error:
            print(f"Warning: hostname command returned error: {error}")
        
        if hostname:
            return hostname
        else:
            return f"VM-{ip}"
    
    except Exception as e:
        print(f"SSH connection failed for hostname: {e}")
        return f"VM-{ip}"
    
    finally:
        ssh.close()

def get_previous_status(status_file: Path):
    if status_file.exists():
        with open(status_file, "r", encoding="utf-8") as f:
            return f.read().strip() == "online"
    return None

def save_status(status_file: Path, online: bool):
    with open(status_file, "w", encoding="utf-8") as f:
        f.write("online" if online else "offline")


# main logic

if __name__ == "__main__":
    STATUS_FILE = Path(__file__).parent / "server_ssh_status.txt"

    # Получаем настоящее имя виртуалки
    SERVER_NAME = get_vm_hostname(SERVER_IP, SSH_USER, SSH_PASSWORD, SSH_PORT)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_online = check_ssh(SERVER_IP, port=SSH_PORT)

    print(f"[{timestamp}] {SERVER_NAME} ({SERVER_IP}:{SSH_PORT}) → {'reachable' if current_online else 'OFFLINE'}")

    previous_online = get_previous_status(STATUS_FILE)

    if previous_online is None:
        status_text = "reachable via SSH" if current_online else "NOT reachable via SSH"
        send_message(
            f"[{timestamp}] 🤖 Bot started monitoring **{SERVER_NAME}** ({SERVER_IP}). "
            f"Initial status: **{status_text}**"
        )
    elif not current_online and previous_online:
        send_message(
            f"[{timestamp}] 🚨 **{SERVER_NAME}** ({SERVER_IP}) is **OFFLINE** (SSH port {SSH_PORT} not responding)"
        )
    elif current_online and not previous_online:
        send_message(
            f"[{timestamp}] ✅ **{SERVER_NAME}** ({SERVER_IP}) is **BACK ONLINE** (SSH port {SSH_PORT} responding)"
        )

    save_status(STATUS_FILE, current_online)