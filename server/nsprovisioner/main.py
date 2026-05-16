# manager runner
import json
import time

from shared.cache import sync_r
from shared.config import NS_RedisProvider
from shared.discovery import get_healthy_runner
from shared.logger import log_event
from shared.worker import celery_app


message_broker = NS_RedisProvider()

def ns_provisioner():
    """
    Main loop for the Provisioner service.
    Runs in its own container and orchestrates the job lifecycle.
    """
    print("Service started. Watching 'job_queue'...")

    while True:
        job_spec = message_broker.pop_job(queue_name="job_queue")
        print(f"DEBUG REDIS RESULT: {job_spec} | TYPE: {type(job_spec)}")

        if job_spec is None:
            continue

        job_id = job_spec.get('job_id')
        log_event(job_id, "[nsprovisioner] Job detected. Finding runner...")

        # find a runner with < 80% load
        runner = get_healthy_runner(max_load=80)

        if not runner:
            log_event(job_id, "[nsprovisioner] No capacity! Re-queueing...")
            # Push back to the end of the queue and wait a bit
            message_broker.push_job(queue_name="job_queue", payload=job_spec)
            time.sleep(2)
            continue

        runner_queue = f"queue-{runner['id']}"
        runner_id = runner['id']
        
        runner_ip = runner.get('ip')

        if not runner_ip:
            print(f"Warning: Runner {runner.get('id')} has a registry entry but no IP yet. Skipping...", flush=True)
            continue

        # register the assignment in Redis for the API to see
        sync_r.hset(
            f"job:registry:{job_id}", 
            mapping={"runner_id": runner_id, "runner_ip": runner_ip, "status": "APPROVED"}
        )

        log_event(job_id=job_id, message=f"[nsprovisioner] Allocated Runner ID: {runner_id} | IP: {runner_ip} | Queue: {runner_queue}")
        celery_app.send_task('tasks.nsrunner', args=[runner['id'], job_spec, False], queue=runner_queue)

if __name__  == "__main__":
    print("Initializing nsprovisioner")
    ns_provisioner()