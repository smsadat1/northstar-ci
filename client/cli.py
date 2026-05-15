import argparse
import requests
import sys
import websocket


def nsci_client_main():

    parser = argparse.ArgumentParser(description="NSCI Job Runner")
    parser.add_argument("--image", default="alpine:latest", help="Container image")
    parser.add_argument("--debug", type=bool, default=False, help="Enable debug mode")
    parser.add_argument("command", help="Command to execute")

    args = parser.parse_args()

    job_spec = {
        "image": str(args.image),
        "command": str(args.command),
        "env": {
            "DEBUG": "1" if args.debug else "0",
            "PROCESSED_AT": "2026-05-15" # Metadata
        }
    }

    res = requests.post(
        url="http://127.0.0.1:8000/jobs/run",
        json=job_spec,
    )
        
    if res.status_code == 200:
        job_id = res.json()['job_id']
        print("\033[32m✔\033[0m Job submitted")
        try:
            ws = websocket.create_connection(f"ws://127.0.0.1:8000/ws/logs/{job_id}")

            while True:
                result = ws.recv()
                if result == "END":
                    try:
                        ws.shutdown() 
                        ws.close()
                    except Exception as e:
                        print(f"Error during close: {e}")
                    finally:
                        return
                    
                print(result)
        
        except websocket.WebSocketConnectionClosedException:
            print("Remote host closed the connection (Server-side drop)")
        except Exception as e:
            print(f"Captured Error: {e}")
    
    elif res.status_code == 401:
        print(res.json()['detail'])
        return
    else:
        print(f"\033[31m✘\033[0m Error from server:", res.status_code)
        return

if __name__ == "__main__":
    nsci_client_main()