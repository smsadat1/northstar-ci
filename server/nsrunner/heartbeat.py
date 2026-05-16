import time
import os
import psutil
import json
from shared.cache import sync_r

RUNNER_ID = os.getenv("RUNNER_ID", "runner-123")
RUNNER_IP = os.getenv("RUNNER_IP", "127.0.0.1")

def send_hearbeat():

    while True: 
        try: 
            cpu_load = psutil.cpu_count()
            mem_load = psutil.virtual_memory().percent

            payload = {
                "id": RUNNER_ID,
                "ip": RUNNER_IP,
                "load": max(cpu_load, mem_load),                    # type: ignore
                "status": "HEALTHY" if cpu_load < 85 else "BUSY"    # type: ignore
            }
            # Write to Redis with an absolute 15 second expiration
            sync_r.setex(f"runner:registry:{RUNNER_ID}", 15, json.dumps(payload))
        except Exception as e:
            print(f"Heartbeat failed to report: {e}")

        time.sleep(5)
