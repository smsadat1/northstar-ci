from registry import nsrrt

from shared.config import sync_r
from shared.worker import celery_app
from shared.config import message_broker
from shared.logger import log_event


def dispatch_job(job_spec):

    job_id = job_spec['job_spec']
    runner_id = nsrrt.get_healthy_runner(region='Singapore')
    runner_queue = f"queue-{runner_id}"

    if not runner_id:
        log_event(job_id, "[nsprovisioner] No capacity available! Re-queueing...")
        # Push back to the end of the queue if no suitable runner found
        message_broker.push_job(queue_name="job_queue", payload=job_spec)

    log_event(job_id, f"[nsprovisioner] Selected runner {runner_id} for Job {job_id}")

    # send task via celery
    celery_app.send_task(
        'tasks.nsrunner', args=[job_spec, runner_id, False], queue=runner_queue, 
        ignore_result=True # prevents synchronous connection blocking
    )

    # signal via grpc, this wakes up the async gRPC thread waiting right next to it in memory
    target_channel = f"signals:runner:{runner_id}"
    sync_r.publish(target_channel, job_id)
    
    print(f"[Signal Engine] Interruption event broadcasted down {target_channel} for Job {job_id}")
    return True