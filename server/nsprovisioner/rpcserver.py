import asyncio
from concurrent import futures
import grpc
from grpc import aio

from cache import async_r
from dispatcher import nsrrt
from registry import NSRRT_Schema

from shared.rpc import coordinator_pb2
from shared.rpc import coordinator_pb2_grpc


class NSControlPlaneServicer(coordinator_pb2_grpc.NSControlPlaneServicer):
    
    async def EstablishControlChannel(self, request_iterator, context):
        """
        The gRPC interface stays ASYNC to allow thousands of runners 
        to hold open multiplexed streaming connections concurrently.
        """
        runner_id = None
        pubsub = async_r.pubsub()

        async def read_heartbeats():
            nonlocal runner_id

            try:
                async for heartbeat in request_iterator:
                    runner_id = heartbeat.runner_id
                    entry = NSRRT_Schema(
                        runner_id=runner_id,
                        runner_ip='',
                        region=heartbeat.region,
                        current_job=heartbeat.current_job_id,
                        queue_len=heartbeat.queue_len,
                        ema_velocity=heartbeat.ema_velocity,
                        backlog_scope=heartbeat.backlog_scope,
                    )

                    nsrrt.upsert_nsrrt(runner_id=runner_id, entry=entry)

            except grpc.RpcError as e:
                print(f"Runner {runner_id} disconnected from stream channel: {e}")

        heartbeat_task = asyncio.create_task(read_heartbeats())

        try: 
            # wait for a while till a runner comes
            while runner_id is None:
                await asyncio.sleep(0.1)

            runner_signal_channel = f'signals:runner:{runner_id}'
            await pubsub.subscribe(runner_signal_channel)
            print(f"[gRPC-Out] Active outbound channel initialized for: {runner_id}")

            while context.is_active():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'message':
                    job_spec = message['data']
                    job_id = job_spec['job_id']

                    yield
                    coordinator_pb2.NSTaskAssignment(
                        status="TASK_ASSIGNED", job_id=job_id,
                        assign_msg=f"Wake up. Task {job_id} is sitting in your Celery queue."
                    )

        except grpc.RpcError as e:
            print(f"Runner {runner_id} network channel severed: {e}")
        finally:
            await pubsub.unsubscribe()
            heartbeat_task.cancel()
            await async_r.close()


async def init_nsp_grpc_server():
    """
    Bootstraps the synchronous gRPC thread pool server.
    Lives inside a background daemon thread.
    """
    server = aio.server()
    coordinator_pb2_grpc.add_NSControlPlaneServicer_to_server(NSControlPlaneServicer(), server)

    server.add_insecure_port("[::]:50051")
    await server.start()
    print("nsprovisioner grpc server started in port 50051")

    # block this thread continuously to keep the channel pipes open
    await server.wait_for_termination()


def start_grpc_thread_loop(loop):
    """
    Helper to establish and keep an isolated asyncio loop running 
    inside your background worker daemon thread.
    """
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_nsp_grpc_server())