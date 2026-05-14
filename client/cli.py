import requests
import sys
import websocket

def nsci_client_main():

    args = sys.argv[1:]

    if not args: 
        print("Usage: nsci <command>")
        return
    
    cmd = args[0]

    if cmd == "run":
        command_string = sys.argv[2]
        data = {"command": str(command_string)}

        res = requests.post(
            url="http://127.0.0.1:8000/jobs/run",
            json=data,
        )
        
        if res.status_code == 200:
            job_id = res.json()['job_id']
            print(f"\033[32m✔\033[0m Job sent successfully\n\033[37mⓘ\033[0m Job ID: {job_id}")

            try:
                ws = websocket.create_connection(f"ws://127.0.0.1:8000/ws/logs/{job_id}")
                while True:
                    result = ws.recv()
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

    else:
        print("Not implemented or unknown command")


if __name__ == "__main__":
    nsci_client_main()