import json
import time
import subprocess


from logger import log_event
from worker import celery_app


NS_CI_JOB_TIMEOUT = 300
MAX_LINES = 5000


@celery_app.task
def ns_runner(job_data):
   
    job_id = job_data['job_id']

    log_event(job_id, "[nsrunner] Initializing sandbox environment...")

    # construct nerdctl command with all CI restrictions
    cmd = [
        "/usr/local/bin/nerdctl", "run", "--rm",
        "--runtime", "runsc",           # Use gVisor
        "--cpus", "1",                  # CPU Limit
        "--memory", "1024m",            # RAM Limit
        "--pids-limit", "100",          # Fork limit
        "--net", "none",                # Network isolation
        "--read-only",                  # Read-only root FS
        "alpine:latest", 
        "/bin/sh", "-c", job_data['command']
    ]

    proc = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )

    log_event(job_id, "[nsrunner] Running 'nerdctl' (includes pull & exec)...")
        
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
                    log_event(job_id, "[nsrunner] ERROR: Too many log lines. Terminating.")
                    break
                log_event(job_id, line.strip())

            # Check if process ended
            if line == "" and proc.poll() is not None:
                break

            # Kill process if it exceeds time limit
            if time.time() - start_time > NS_CI_JOB_TIMEOUT:
                proc.kill()
                log_event(job_id, "[nsrunner] TIMEOUT: Process forcibly terminated.")
                break

    finally:
        if proc.stdout:
            proc.stdout.close()
    return_code = proc.wait()

    log_event(job_id, f"[nsrunner] finished (exit code {return_code})")