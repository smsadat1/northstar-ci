import asyncio
import grpc
import sys

from .envs import RUNNER_ID, TELEMETRY_BUFFER
from .telemertry import telemetry_bridge
from shared.rpc import coordinator_pb2, coordinator_pb2_grpc
from shared.worker import celery_app


async def push_heartbeats(request_writer):
    """Loop 1: Wakes up instantly when data lands in the manager's queue."""  
    # pull the initialized queue directly out of the manager class context
    buffer_queue = telemetry_bridge.get_buffer()  
    while True:
        try:
            # gather telemetry parameters
            heartbeat_frame = await buffer_queue.get()
            await request_writer.write(heartbeat_frame)
            buffer_queue.task_done()
            
        except Exception as e:
            print(f"Telemetry stream push failed: {e}")
            break


async def listen_tasks(response_reader):
    """Loop 2: Blocks on the incoming gRPC wire waiting for tasks to wake up."""
    async for assignment in response_reader:
        print(f"Signal Received -> Job ID: {assignment.job_id} | Repo: {assignment.repo_name}")
        
        # trigger Celery to inspect its local queue and execute this specific task ID
        celery_app.send_task(
            'tasks.nsrunner',
            args=[assignment.job_id, assignment.pre_signed_s3_url],
            task_id=assignment.job_id # ties Celery tracking straight to global job ID
        )

async def maintain_control_plane_stream(channel):
    """
    This function owns the actual life of the open streaming pipe.
    It runs forever listening to or sending signals.
    """
    print("Control Plane stream session initialized. Initializing heartbeats...")
    
    # Instantiate your proto stubs using the active channel
    # stub = coordinator_pb2_grpc.NSControlPlaneStub(channel)
    
    while True:
        # Keep your async loop busy processing heartbeats or checking telemetry_bridge
        await asyncio.sleep(1.0)


async def connect_to_nsprovisioner(
    server_address = 'nsprovisioner:50051', max_retries=10, initital_delay=1.0
):
    """
    Attempts to establish an async channel to the provisioner.
    Retries gracefully if the server is still booting up.
    """

    delay = initital_delay
    print(f"Initializing Control Plane connection loop targeting: {server_address}")

    for connection_attemp in range(1, max_retries+1):
        try:
            # Instantiate the async channel context
            channel = grpc.aio.insecure_channel(server_address)
            await asyncio.wait_for(channel.channel_ready(), timeout=2.0)  # wait for a while to get connection
            print(f"Successfully linked to gRPC Control Plane on attempt {connection_attemp}!")
            await maintain_control_plane_stream(channel)
            return
            
        except (grpc.aio.AioRpcError, asyncio.TimeoutError) as e:
            print(f"[Attempt {connection_attemp}/{max_retries}] Control Plane not ready yet (Connection Refused). Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay = delay * 2

    print(f"\nFATAL: nsprovisioner at {server_address} remained unreachable after {max_retries} attempts.")
    print("Verify your network configurations and container allocation tables.")
    sys.exit(1)