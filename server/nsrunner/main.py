import asyncio
import threading

from .envs import RUNNER_ID
from .server import connect_to_nsprovisioner
from .telemertry import telemetry_bridge
from shared.worker import celery_app

def start_grpc_thread():
    """Background target that handles the async event loop lifecycle."""
    
    # create dedicated event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # register loop with state-machine bridge so the sync Celery worker can thread-safely send metrics to it later
    telemetry_bridge.register_loop(loop)

    # block this background thread running async gRPC engine
    loop.run_until_complete(connect_to_nsprovisioner())



if __name__ == "__main__":

    # boot grpc server and send a registry payload
    print(f"[nsrunner] Launching gRPC background thread...")
    grpc_thread = threading.Thread(target=start_grpc_thread, daemon=True)
    grpc_thread.start()

    print(f"[nsrunner] Step 2: Dispatching initial zeroed registration heartbeat...")
    telemetry_bridge.send(
        runner_id=RUNNER_ID, job_id='', region='Singapore',
        queue_len=0, ema_velocity=0.0, backlog_scope=0.0
    ) 

    print(f"[nsrunner] Instantiating Celery Worker object programmatically...")
    worker = celery_app.Worker(
        queues=[f'queue-{RUNNER_ID}'],
        loglevel='INFO',
        optimization='fair' # for isolated job execution
    )
    
    # start the worker loop. This blocks the main thread permanently
    # while the gRPC thread manages bi-directional heartbeat stream in the background
    worker.start()