import os
import shutil
import subprocess
import time 

from .envs import MAX_LINES, NS_CI_JOB_TIMEOUT
from shared.logger import log_event


def nsrunner_execute(job_id, runner_id, container_name, workspace_dir, cmd):

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
        
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

        print(f"Executing guaranteed low-level teardown for {container_name}")
        os.system(f"docker kill {container_name} > /dev/null 2>&1")
        os.system(f"docker rm -f {container_name} > /dev/null 2>&1")

    return_code = proc.wait()

    log_event(job_id, f"[nsrunner:{runner_id}] Cleaning artifacts")
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)

    log_event(job_id, f"[nsrunner:{runner_id}] finished (exit code {return_code})")
    log_event(job_id, f"END")
    

