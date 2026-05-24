import os
import json
import shutil
import time
import subprocess

from .cmdbuilder import ns_build_stage_cmd, ns_run_stage_cmd
from .execution import nsrunner_execute
from shared.logger import log_event
from shared.worker import celery_app



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
    container_name = f"sandbox-{runner_id}-{job_id}"

    log_event(job_id, f"[nsrunner:{runner_id}] Initializing sandbox environment...")
    log_event(job_id, f"[nsrunner:{runner_id}] Starting container tasks...")

    # build stage command and execution
    build_cmd = ns_build_stage_cmd(container_name, job_spec, workspace_dir)
    nsrunner_execute(
        job_id=job_id, runner_id=runner_id, 
        container_name=container_name, workspace_dir=workspace_dir, 
        cmd=build_cmd
    )
    
    run_cmd = ns_run_stage_cmd(container_name, job_spec, workspace_dir)
    nsrunner_execute(
        job_id=job_id, runner_id=runner_id, 
        container_name=container_name, workspace_dir=workspace_dir, 
        cmd=run_cmd
    )