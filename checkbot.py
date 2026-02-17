import os
import random
import time
from datetime import datetime
from dotenv import load_dotenv
import zulip

# load environment variables from check.env
env_path = r"C:\Users\o165i\Pythonprojects\check.env"
load_dotenv(dotenv_path=env_path)

# check of env file
print("EMAIL:", os.getenv("ZULIP_EMAIL"))
print("API KEY:", os.getenv("ZULIP_API_KEY"))
print("SITE:", os.getenv("ZULIP_SITE"))
print("STREAM:", os.getenv("STREAM"))
print("TOPIC:", os.getenv("TOPIC"))

# creating Zulip client 
client = zulip.Client(   #object which can send messages thru the Zulip API
    email=os.getenv("ZULIP_EMAIL"),
    api_key=os.getenv("ZULIP_API_KEY"),
    site=os.getenv("ZULIP_SITE")
)

STREAM = os.getenv("STREAM") #just saying to bot to where he has to send messages
TOPIC = os.getenv("TOPIC") 

def send_message(content):
    """Send a message to the specified Zulip stream and topic"""
    request = {
        "type": "stream",
        "to": STREAM,
        "topic": TOPIC,
        "content": content  #kinda vocabulary for easier usage 
    }
    client.send_message(request)
    print(f"Sent: {content}")

def simulate_server():
    """Simulate server activity with random errors"""
    while True:
        time.sleep(5)
        if random.randint(1, 100) <= 30:  # 30% chance of error
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_message = f"[{timestamp}] 🚨 Server error detected!"
            send_message(error_message)
        else:
            print("Server is running normally.")

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_message(f"[{timestamp}] 🤖 Bot started and ready!")
    simulate_server() #to show is VM online, to show the name of VM which was interupted
