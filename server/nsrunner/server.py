import asyncio
import socket
import grpc 

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


async def run_orchestrator():

    current_loop = asyncio._get_running_loop()
    telemetry_bridge.register_loop(current_loop)

    async with grpc.aio.insecure_channel('nsprovisioner:9901') as channel:
        print('Initializing gRPC server')
        stub = coordinator_pb2_grpc.NSControlPlaneStub(channel)
        stream = stub.EstablishControlChannel()
        await asyncio.gather(push_heartbeats(stream), listen_tasks(stream))
