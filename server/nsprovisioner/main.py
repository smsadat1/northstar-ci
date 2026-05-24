import asyncio
import json
import time

from dispatcher import dispatch_job
from rpcserver import start_grpc_thread_loop
import threading


from shared.config import NS_RedisProvider, sync_r
from shared.logger import log_event
from shared.worker import celery_app


message_broker = NS_RedisProvider()

def start_nsprovisioner():
    """
    Main loop for the nsprovisioner service.
    Runs in its own container and orchestrates the job lifecycle.
    """
    print("nrovisioner active. Listening to global job_queue...")

    while True:
        job_spec = message_broker.pop_job(queue_name="job_queue")

        if job_spec is None:
            continue

        print(f"DEBUG REDIS RESULT: {job_spec} | TYPE: {type(job_spec)}")

        # Ensure safe extraction whether broker outputs a dict or stringified JSON
        if isinstance(job_spec, str):
            try:
                job_spec = json.loads(job_spec)
            except Exception:
                print("Failed to parse incoming job queue payload string!")
                continue

        job_id = job_spec.get('job_id')
        log_event(job_id, "[nsprovisioner] Job detected. Finding runner...")

        dispatch_job(job_spec=job_spec)

if __name__  == "__main__":
    
    print("Initializing nsprovisioner control plane setup...")
    
    print("Launching gRPC background ingestion thread...")
    grpc_event_loop = asyncio.new_event_loop()
    grpc_thread = threading.Thread(
        target=start_grpc_thread_loop, 
        args=(grpc_event_loop,), daemon=True
    )
    grpc_thread.start()

    # wait a while to let the socket binf
    time.sleep(0.5)

    # Start the blocking master execution pipeline on the main process thread
    print("Initializing nsprovisioner queue worker loop...")
    start_nsprovisioner()