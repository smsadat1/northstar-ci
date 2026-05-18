# builds the cmd
import os 
import shlex

from .utils import download_and_extract_workspace
from shared.logger import log_event
from shared.storage import StorageManager

storage = StorageManager()


def build_nerdctl_cmd(runner_id, job_spec, workspace_dir):
    
    print('Building command for nerdctl')
    job_id = job_spec['job_id']

    cmd = [
        "/usr/local/bin/nerdctl", "run", "--rm",
        "--name", runner_id,            # unique naming
        "--runtime", "runsc",           # Use gVisor
        "--net", "none",                # Network isolation
    ]

    # add env vars
    if "env" in job_spec:
        for key, value in job_spec['env'].items():
            cmd.extend(["--env", f"{key}={value}"])

    # resource limits
    cmd.extend([
        "--cpus", "1", "--memory", "1024m",
        "--pids-limit", "100", "--net", "none",
        "--read-only",
    ])

    print(f"[nsrunner DEBUG] job_spec payload keys: {list(job_spec.keys())}")
    print(f"[nsrunner DEBUG] value of has_file: {job_spec.get('has_file')} (Type: {type(job_spec.get('has_file'))})")

    if job_spec.get('has_file'):
        log_event(job_id, "[nsrunner] downloading workspace from object storage...")
        
        download_and_extract_workspace(storage_client=storage, job_id=job_id, workspace_dir=workspace_dir)

        log_event(job_id, f"[nsrunner]  Files extracted: {os.listdir(workspace_dir)}")
        # mount the directory and set it as the working directory inside the container
        # Note: Even with --read-only rootfs, mounted volumes remain writable unless specified as :ro
        cmd.extend(["-v", f"{workspace_dir}:/workspace", "-w", "/workspace"])

    cmd.append(job_spec["image"])
    cmd.extend([*shlex.split(job_spec.get('command'))])

    return cmd
        