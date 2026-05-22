import argparse
import requests
from pathlib import Path
import json
import os
import io
import tarfile
import websocket

from parser import parse_yaml_to_json


def nsci_client_main():

    parser = argparse.ArgumentParser(description="NSCI Job Runner")
    parser.add_argument("--config", help="YAML or JSON file to use")
    parser.add_argument("--repo", help="Target remote git repository")

    args = parser.parse_args()

    if args.config:
        json_data = parse_yaml_to_json(args.config)
    else:
        print('[nsclient] No config file provided')
        return

    target = json_data.get('target_file')

    if isinstance(target, str) and target.strip():
        file_path = Path(target)
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            clean_filename = os.path.basename(args.input)
            tar.add(args.input, arcname=clean_filename)

        # Move buffer pointer back to the beginning of the stream
        tar_buffer.seek(0)

    # Payload payload needs to be packaged for multipart/form-data
    payload = {"job_spec_str": json.dumps(json_data)}
    
    res = requests.post(url="http://127.0.0.1:8000/jobs/run", data=payload)

    
    if res.status_code == 200:

        data = res.json()

        job_id = data['job_id']
        s3_upload_url = data['s3_upload_url']

        # LOCAL TESTING PATCH: Swap out Docker's internal container name for 'localhost'
        if s3_upload_url:
            if "http://storage:9000" in s3_upload_url:
                s3_upload_url = s3_upload_url.replace("http://storage:9000", "http://localhost:9000")
            elif "http://ns-storage-bucket.storage:9000" in s3_upload_url:
                s3_upload_url = s3_upload_url.replace(
                    "http://ns-storage-bucket.storage:9000", 
                    "http://localhost:9000/ns-storage-bucket"
                )

            local_tarball_path = f"/tmp/{job_id}.tar.gz"
            print(f"[ns-cli] Compressing {file_path} into {local_tarball_path}...")

            with tarfile.open(local_tarball_path, "w:gz") as tar:
                tar.add(file_path, arcname=os.path.basename(file_path))

            print("[ns-cli] Initializing direct upload to storage...")

            print(f'URL client has for s3: {s3_upload_url}')
            with open(local_tarball_path, "rb") as raw_file: 
                upload_res = requests.put(url=s3_upload_url, data=raw_file,
                    headers={"X-Amz-Content-SHA256": "UNSIGNED-PAYLOAD"})

                if upload_res.status_code == 200:
                    print("\n[ns-cli] Success! Upload finished, received 200 OK.")
                else:
                    print(f"\n[ns-cli] Error: Direct upload failed with status {upload_res.status_code}")
            
            print(f"\033[32m✔\033[0m File sent successfully\n\033[37mⓘ\033[0m Job ID: {job_id}")
        else:
            print(f"\033[32m✔\033[0m Job sent successfully\n\033[37mⓘ\033[0m Job ID: {job_id}")

    elif res.status_code == 401:
        print(res.json()['detail'])
        return
    else:
        print(f"\033[31m✘\033[0m Error from server:", res.status_code)
        return
        
    if res.status_code == 200:
        print("\033[32m✔\033[0m Job submitted")
        try:
            ws = websocket.create_connection(f"ws://127.0.0.1:8000/ws/logs/{job_id}")

            try:
                while True:
                    result = ws.recv()
                    print(result)
            except websocket.WebSocketConnectionClosedException:
                print("Server closed connection")
            finally:
                ws.close()
                print("closed:", ws.connected)
        
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