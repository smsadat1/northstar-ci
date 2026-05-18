import argparse
import requests
import json
import os
import io
import sys
import tarfile
import websocket


class ProgressFileReader:
    """Wraps a file object to calculate progression as chunks stream out."""
    def __init__(self, filepath):
        self.filename = os.path.basename(filepath)
        self.file_size = os.path.getsize(filepath)
        self.file_object = open(filepath, "rb")
        self.bytes_read = 0

    def read(self, chunk_size=-1):
        data = self.file_object.read(chunk_size)
        if data:
            self.bytes_read += len(data)
            percent = (self.bytes_read / self.file_size) * 100
            
            # Print a dynamic progress bar directly to stdout
            bar_length = 30
            filled_length = int(round(bar_length * self.bytes_read / float(self.file_size)))
            bar = '=' * filled_length + '-' * (bar_length - filled_length)
            
            sys.stdout.write(f"\r[ns-cli] Uploading {self.filename}: [{bar}] {percent:.1f}% complete")
            sys.stdout.flush()
        return data

    def __len__(self):
        return self.file_size

    def close(self):
        self.file_object.close()


def nsci_client_main():

    parser = argparse.ArgumentParser(description="NSCI Job Runner")
    parser.add_argument("input_file", help="File to read")
    parser.add_argument("--image", default="alpine:latest", help="Container image")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("command", help="Command to execute")

    args = parser.parse_args()

    file_name = os.path.basename(args.input_file)

    job_spec = {
        "command": str(args.command),
        "image": str(args.image),
        "has_file": True if args.input_file else False,
        "env": {
            "DEBUG": "1" if args.debug else "0",
            "PROCESSED_AT": "2026-05-15" 
        }
    }

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        clean_filename = os.path.basename(args.input_file)
        tar.add(args.input_file, arcname=clean_filename)

    # Move buffer pointer back to the beginning of the stream
    tar_buffer.seek(0)

    # Payload payload needs to be packaged for multipart/form-data
    payload = {"job_spec_str": json.dumps(job_spec)}
    
    res = requests.post(url="http://127.0.0.1:8000/jobs/run", data=payload)

    
    if res.status_code == 200:
        job_id = res.json()['job_id']
        s3_upload_url = res.json()["s3_upload_url"]

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
            print(f"[ns-cli] Compressing {file_name} into {local_tarball_path}...")

            with tarfile.open(local_tarball_path, "w:gz") as tar:
                tar.add(file_name, arcname=os.path.basename(file_name))

        print("[ns-cli] Initializing direct upload to storage...")
        wrapped_file = ProgressFileReader(local_tarball_path)

        try:
            upload_res = requests.put(
                url=s3_upload_url, data=wrapped_file, 
                headers={"Content-Type": "application/gzip", "Host": "storage:9000"}
            )
        
            if upload_res.status_code == 200:
                print("\n[ns-cli] Success! Upload finished, received 200 OK.")
            else:
                print(f"\n[ns-cli] Error: Direct upload failed with status {upload_res.status_code}")
            
        finally:
            wrapped_file.close()
    elif res.status_code == 401:
        print(res.json()['detail'])
        return
    else:
        print(f"\033[31m✘\033[0m Error from server:", res.status_code)
        return
        
    if upload_res.status_code == 200:
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