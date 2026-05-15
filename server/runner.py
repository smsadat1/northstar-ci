import json
import time
import subprocess

from cmdbuilder import build_nerdctl_cmd
from logger import log_event
from worker import celery_app


NS_CI_JOB_TIMEOUT = 300
MAX_LINES = 5000


@celery_app.task(bind=True, max_retries=5)
def ns_runner(self, runner_id, job_spec, retries: bool):
   
    if retries:
        raise self.retry(countdown=10)

    job_id = job_spec['job_id']

    log_event(job_id, f"[nsrunner:{runner_id}] Initializing sandbox environment...")

    cmd = build_nerdctl_cmd(runner_id, job_spec)

    proc = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )

    log_event(job_id, f"[nsrunner:{runner_id}] Starting container tasks...")
        
    # iterate over output line by line
    start_time = time.time()
    line_count = 0
    
    try:
        while True:
            line = proc.stdout.readline() # type: ignore
            if line:
                line_count += 1
                if line_count > MAX_LINES:
                    proc.kill()
                    log_event(job_id, f"[nsrunner:{runner_id}] ERROR: Too many log lines. Terminating.")
                    break
                log_event(job_id, line.strip())

            # Check if process ended
            if line == "" and proc.poll() is not None:
                break

            # Kill process if it exceeds time limit
            if time.time() - start_time > NS_CI_JOB_TIMEOUT:
                proc.kill()
                log_event(job_id, f"[nsrunner:{runner_id}] TIMEOUT: Process forcibly terminated.")
                break

    finally:
        if proc.stdout:
            proc.stdout.close()
    return_code = proc.wait()

    log_event(job_id, f"[nsrunner:{runner_id}] finished (exit code {return_code})")
    log_event(job_id, f"END")