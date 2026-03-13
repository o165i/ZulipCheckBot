import os
import socket
import paramiko
from datetime import datetime
from dotenv import load_dotenv
import zulip
from pathlib import Path
import time
import subprocess
import json

# Load environment variables
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print("❌ .env file not found!")
    exit(1)

load_dotenv(dotenv_path=env_path)

client = zulip.Client(
    email=os.getenv("ZULIP_EMAIL"),
    api_key=os.getenv("ZULIP_API_KEY"),
    site=os.getenv("ZULIP_SITE")
)

STREAM = os.getenv("STREAM")  # e.g. "bot test"
CHECK_INTERVAL = 30  # seconds between checks

class ServerMonitor:
    def __init__(self, ip: str = None, username: str = None, password: str = None, ssh_port: int = 22):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh_port = ssh_port
        self.status_file = Path(__file__).parent / f"status_{ip.replace('.', '_')}.txt" if ip else None
        self.server_name = None
        self.last_container_status = {}  # container name → state

    def get_server_name(self):
        """Fetch server hostname via SSH or locally"""
        if self.server_name is not None:
            return self.server_name

        if not self.ip:
            # Local VM
            try:
                with open("/etc/hostname", "r") as f:
                    hostname = f.read().strip()
                    self.server_name = hostname if hostname else "localhost"
                    return self.server_name
            except:
                self.server_name = "unknown-local"
                return self.server_name

        # Remote VM via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname=self.ip,
                port=self.ssh_port,
                username=self.username,
                password=self.password,
                timeout=6,
                allow_agent=True,
                look_for_keys=True
            )
            _, stdout, _ = ssh.exec_command("hostname")
            hostname = stdout.read().decode().strip()
            if hostname:
                self.server_name = hostname
                return hostname
            else:
                self.server_name = f"unknown-{self.ip}"
                return self.server_name
        except Exception as e:
            print(f"[DEBUG] Failed to get hostname: {e}")
            self.server_name = f"unknown-{self.ip}"
            return self.server_name
        finally:
            ssh.close()

    def check_ssh(self, timeout=3):
        if not self.ip:
            return True  # local VM always "online"
        try:
            with socket.create_connection((self.ip, self.ssh_port), timeout=timeout):
                return True
        except:
            return False

    def check_containers(self):
        """Get status of all Docker containers (local or via SSH)"""
        if self.ip:
            # Remote VM via SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(
                    hostname=self.ip,
                    port=self.ssh_port,
                    username=self.username,
                    password=self.password,
                    timeout=6,
                    allow_agent=True,
                    look_for_keys=True
                )
                _, stdout, stderr = ssh.exec_command("docker ps -a --format '{{json .}}'")
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                if error:
                    print(f"[DEBUG] Docker ps error: {error}")
                    return {}
                containers = [json.loads(line) for line in output.splitlines() if line.strip()]
            finally:
                ssh.close()
        else:
            # Local VM
            try:
                output = subprocess.check_output(["docker", "ps", "-a", "--format", "{{json .}}"], text=True)
                containers = [json.loads(line) for line in output.splitlines() if line.strip()]
            except Exception as e:
                print(f"[DEBUG] Local docker ps error: {e}")
                containers = []

        status = {}
        for c in containers:
            name = c["Names"]
            state = c["State"]
            status[name] = {
                "state": state,
                "status": c["Status"],
                "id": c["ID"]
            }
        return status

    def send_message(self, content: str):
        topic_name = self.get_server_name()

        request = {
            "type": "stream",
            "to": STREAM,
            "topic": topic_name,
            "content": content
        }

        print(f"[DEBUG] Sending to stream '{STREAM}', topic '{topic_name}'")

        try:
            result = client.send_message(request)
            print(f"[DEBUG] Zulip response: {result}")
        except Exception as e:
            print(f"[DEBUG] Send error: {e}")

    def check_once(self):
        real_name = self.get_server_name()
        current_online = self.check_ssh()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        previous_online = None
        if self.status_file:
            if self.status_file.exists():
                with open(self.status_file, "r", encoding="utf-8") as f:
                    previous_online = f.read().strip() == "online"

            print(f"[{timestamp}] {real_name} ({self.ip or 'local'}) → {'ONLINE' if current_online else 'OFFLINE'}")

            if previous_online is None or current_online != previous_online:
                if previous_online is None:
                    msg = f"[{timestamp}] 🤖 Monitoring started for **{real_name}** ({self.ip or 'local'})\nVM Status: **{'reachable' if current_online else 'unreachable'}**"
                elif not current_online:
                    msg = f"[{timestamp}] 🚨 **{real_name}** ({self.ip or 'local'}) is **UNREACHABLE**"
                else:
                    msg = f"[{timestamp}] ✅ **{real_name}** ({self.ip or 'local'}) is **BACK ONLINE**"
                self.send_message(msg)

            if self.status_file:
                with open(self.status_file, "w", encoding="utf-8") as f:
                    f.write("online" if current_online else "offline")

        # Docker containers check (only if VM is reachable)
        if current_online:
            containers = self.check_containers()
            for name, current in containers.items():
                prev_state = self.last_container_status.get(name)
                if prev_state is None:
                    # First time seen
                    msg = f"[{timestamp}] New container **{name}** detected on **{real_name}**\nStatus: {current['state']} ({current['status']})"
                    self.send_message(msg)
                elif prev_state != current["state"]:
                    # State changed
                    msg = f"[{timestamp}] Container **{name}** on **{real_name}** changed:\n"
                    msg += f"Was: {prev_state} → Now: {current['state']} ({current['status']})"
                    self.send_message(msg)

                self.last_container_status[name] = current["state"]

def main():
    print(f"🚀 Continuous monitoring started...\n")

    monitors = [
        ServerMonitor(  # remote VM
            ip="192.168.56.101",
            username="o165i",
            password="Saneck228!!",
            ssh_port=22
        ),
        ServerMonitor(  # local VM (no SSH, monitor local containers)
            ip=None,
            username=None,
            password=None
        ),
        #ServerMonitor(  # remote VM
         #   ip="192.168.56.102",
          #  username="o165i",
           # password="Saneck2281337!!",
            #ssh_port=22
        #),
    ]

    while True:
        for monitor in monitors:
            monitor.check_once()
        print(f"\n[INFO] Sleeping for {CHECK_INTERVAL} seconds... (Ctrl+C to stop)")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()