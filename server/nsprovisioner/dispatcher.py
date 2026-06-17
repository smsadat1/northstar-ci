from registry import nsrrt
from translator import expand_job_spec

from shared.config import message_broker
from shared.logger import log_event


def dispatch_job(job_spec):

    """
    queues tasks locally for the target nsrunner instance to pull down later
    """
    owner_id = job_spec['owner_id']
    job_id = job_spec['pipeline_id']
    runner_id, runner_ip = nsrrt.get_associated_runner(owner_id=owner_id)

    if not owner_id: 
        log_event(job_id, "[nsprovisioner] Invalid owner (probably orphaned)")
        # Push back to the end of the queue if no suitable runner found
        message_broker.push_job(queue_name="job_queue", payload=job_spec)
        return False

    if not runner_id:
        log_event(job_id, "[nsprovisioner] No capacity available! Re-queueing...")
        # Push back to the end of the queue if no suitable runner found
        message_broker.push_job(queue_name="job_queue", payload=job_spec)
        return False
    
    log_event(job_id, f"[nsprovisioner] Selected runner {runner_id} for Job {job_id}")

    # expand job & send task via celery
    nsr_tasks = expand_job_spec(job_spec_data=job_spec)

    # integrate grpc here
    for nsr_task in nsr_tasks:
        message_broker.push_job(queue_name=f'tasks:{runner_id}', payload=nsr_task.model_dump())

    return True