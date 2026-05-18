import os
import json
import shutil
import time
import subprocess

from .cmdbuilder import build_nerdctl_cmd
from shared.config import message_broker
from shared.logger import log_event
from shared.worker import celery_app


NS_CI_JOB_TIMEOUT = 300
MAX_LINES = 5000


@celery_app.task(name="tasks.nsrunner", bind=True, max_retries=5)
def ns_runner(self, job_spec, runner_id, retries: bool):
   
    if retries:
        raise self.retry(countdown=10)

    if not job_spec:
        print('Job spec not found')
        return
    
    if isinstance(job_spec, str):
        job_spec = json.loads(job_spec)
        
    job_id = job_spec['job_id']
    workspace_dir = f"/tmp/workspaces/{job_id}"

    log_event(job_id, f"[nsrunner:{runner_id}] Initializing sandbox environment...")

    cmd = build_nerdctl_cmd(runner_id, job_spec, workspace_dir=workspace_dir)

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
                log_event(job_id, line.strip(), exec_logs=True)

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

    log_event(job_id, f"[nsrunner:{runner_id}] Cleaning artifacts")
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)

    log_event(job_id, f"[nsrunner:{runner_id}] finished (exit code {return_code})")
    log_event(job_id, f"END")