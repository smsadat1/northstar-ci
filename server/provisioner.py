# manager runner
import psutil

from logger import log_event
from runner import ns_runner


def ns_provisioner(job_spec):
    runner_id = f"runner-{job_spec['job_id'][:8]}"
    log_event(job_id=job_spec['job_id'], message=f"[nsserver] Runner ID: {runner_id}")

    # Check system load (avg of 1, 5 and 15 mins)
    load_1, load_5, load_15 = psutil.getloadavg()
    cpu_count = psutil.cpu_count()

    if cpu_count:
        usage_pct = (load_1 / cpu_count) * 100

    if usage_pct > 80:
        log_event(job_id=job_spec['job_id'], message="[nsserver] Server too busy! Delaying job.")
        ns_runner.delay(runner_id, job_spec, True)
    else:
        ns_runner.delay(runner_id, job_spec, False)
    
    return runner_id