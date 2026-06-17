import logging
from concurrent import futures

import grpc, time

from shared.config import message_broker
from shared.logger import log_event

from pb import comms_pb2 as pb2
from pb import comms_pb2_grpc as pb2_grpc
from registry import nsrrt, NSRRT_Schema

class TaskQueueServicer(pb2_grpc.TaskQueueServiceServicer):
    
    def FetchNextTask(self, request, context):
        """
        triggered when a Go runner pulls for work.
        reads non-blockingly from the nsrunner's dedicated task queue.
        """
        runner_id = request.runner_id
        owner_id = request.owner_id
        queue_name = f"tasks:{runner_id}"

        logging.info(f"[gRPC server Poll] Runner '{runner_id}' (Owner: {owner_id}) is asking for work.")

        pending_job = message_broker.pop_job(queue_name=queue_name)

        if pending_job:
            logging.info(f"[gRPC Dispatch] Task found! Shipping job to runner {runner_id}")

            # map payload keys safely to strict protobuf types
            task_payload = pb2.NSRTask(
                owner_id=str(pending_job.get('owner_id', '')),
                region=str(pending_job.get('region', '')),
                container_id=str(pending_job.get('container_id', '')),
                s3url=str(pending_job.get('s3url', '')),
                timeout_sec=int(pending_job.get('timeout_sec', 300)),
                memory_limit_mb=int(pending_job.get('memory_limit_mb', 512)),
                max_stdout_kb=int(pending_job.get('max_stdout_kb', 1024)),
                cpu_shares=int(pending_job.get('cpu_shares', 1024)),
                diskt_limits=int(pending_job.get('diskt_limits', 0)),
                lint_runtime=str(pending_job.get('lint_runtime', '')),
                lint_command=str(pending_job.get('lint_command', '')),
                lint_env=dict(pending_job.get('lint_env', {})),
                build_runtime=str(pending_job.get('build_runtime', '')),
                build_command=str(pending_job.get('build_command', '')),
                build_env=dict(pending_job.get('build_env', {})),
                test_runtime=str(pending_job.get('test_runtime', '')),
                test_command=str(pending_job.get('test_command', '')),
                test_env=dict(pending_job.get('test_env', {}))
            )
            return pb2.NSRTaskResponse(has_task=True, task=task_payload)
        
        return pb2.NSRTaskResponse(has_task=False)
    
    def SendHeartBeat(self, request, context):
        """
        triggered when a nsrunner instance pushes its 15-second system performance data.
        upserts the state cleanly inside the redis sidecar table via nsrrt.
        """

        # capture inbound metadata context
        peer_address = context.peer() # e.g., "ipv4:192.168.1.50:41232" or "ipv6:[::1]:52123"

        logging.info(
            f"[gRPC Heartbeat] Inbound payload from {request.runner_id} | "
            f"CPU: {request.cpu_percent:.2f}% | MEM: {request.mem_percent:.2f}% | DISK: {request.disk_percent:.2f}%"
        )

        entry = NSRRT_Schema(
                owner_id=request.owner_id,
                runner_id=request.runner_id,
                runner_ip=str(request.runner_ip if request.runner_ip else peer_address),
                region=request.region,
                cpu_percent=float(request.cpu_percent),
                mem_percent=float(request.mem_percent),
                disk_percent=float(request.disk_percent),
            )

        try: 
            nsrrt.upsert_nsrrt(owner_id=request.owner_id, entry=entry)
        except Exception as e:
            logging.error(f"[nsrrt Error] Failed to commit heartbeat to Redis sidecar: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to write performance records to orchestration routing database.")
            return pb2.NSRTaskResponse(has_task=False)

        # Complete response lifecycle cleanly
        return pb2.NSRTaskResponse(has_task=False)


def server():
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=20))
    pb2_grpc.add_TaskQueueServiceServicer_to_server(TaskQueueServicer(), server=server)
    server.add_insecure_port("[::]:50051")
    logging.info("gRPC Server booting on port [::]:50051")
    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Termination signal intercepted. Stopping server components gracefully...")
        server.stop(grace=5)
        logging.info("gRPC server shut down successfully.")