import os
import socket
import paramiko
from datetime import datetime
from dotenv import load_dotenv
import zulip
from pathlib import Path

# Загрузка .env
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print("❌ .env не найден!")
    exit(1)

load_dotenv(dotenv_path=env_path)

client = zulip.Client(
    email=os.getenv("ZULIP_EMAIL"),
    api_key=os.getenv("ZULIP_API_KEY"),
    site=os.getenv("ZULIP_SITE")
)

STREAM = os.getenv("STREAM")  # "bot test"

class ServerMonitor:
    def __init__(self, ip: str, username: str, password: str = None, ssh_port: int = 22):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh_port = ssh_port
        self.status_file = Path(__file__).parent / f"status_{ip.replace('.', '_')}.txt"
        self.server_name = None

    def get_server_name(self):
        if self.server_name is not None:
            return self.server_name

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
            print(f"[DEBUG] Ошибка получения имени: {e}")
            self.server_name = f"unknown-{self.ip}"
            return self.server_name
        finally:
            ssh.close()

    def check_ssh(self, timeout=3):
        try:
            with socket.create_connection((self.ip, self.ssh_port), timeout=timeout):
                return True
        except:
            return False

    def send_message(self, content: str):
        topic_name = self.get_server_name()

        request = {
            "type": "stream",
            "to": STREAM,
            "topic": topic_name,
            "content": content
        }

        print(f"[DEBUG] Отправка в stream '{STREAM}', topic '{topic_name}'")
        print(f"Сообщение: {content[:100]}...")

        try:
            result = client.send_message(request)
            print(f"[DEBUG] Ответ Zulip: {result}")
            if result.get("result") == "success":
                print(f"[{topic_name}] ✅ Отправлено успешно")
            else:
                print(f"[{topic_name}] ❌ Ошибка от Zulip: {result.get('msg', 'неизвестно')}")
        except Exception as e:
            print(f"[DEBUG] Ошибка отправки: {e}")

    def check_once(self):
        real_name = self.get_server_name()
        current_online = self.check_ssh()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        previous_online = None
        if self.status_file.exists():
            with open(self.status_file, "r", encoding="utf-8") as f:
                previous_online = f.read().strip() == "online"

        print(f"[{timestamp}] {real_name} ({self.ip}) → {'ONLINE' if current_online else 'OFFLINE'}")

        # Временно отправляем ВСЕГДА (для теста)
        msg = f"[{timestamp}] ТЕСТ: {real_name} ({self.ip}) → {'ONLINE' if current_online else 'OFFLINE'}"
        self.send_message(msg)

        # Сохраняем статус
        with open(self.status_file, "w", encoding="utf-8") as f:
            f.write("online" if current_online else "offline")


# ========================
# СПИСОК СЕРВЕРОВ
# ========================
SERVERS = [
    ServerMonitor(
        ip="192.168.56.101",
        username="o165i",
        password="Saneck228!!",
        ssh_port=22
    ),
    ServerMonitor(
        ip="192.168.56.102",
        username="o165i",
        password="Saneck2281337!!",
        ssh_port=22
    ),
]

# ========================
# ЗАПУСК
# ========================
if __name__ == "__main__":
    print(f"🚀 Запуск мониторинга {len(SERVERS)} серверов...\n")
    
    for server in SERVERS:
        server.check_once()
    
    print("\n✅ Все серверы проверены.")