# builds the cmd
import os 

from .utils import download_and_extract_workspace
from shared.logger import log_event
from shared.storage import StorageManager

storage = StorageManager()

MEMORY_HARD_LIMIT = "1024m"


def ns_build_stage_cmd(container_name, job_spec, workspace_dir):
    
    print('Building build stage command for nerdctl')

    job_id = job_spec['job_id']
    log_size = job_spec['build_log_size']
    memory_limit = str(job_spec['build_memory_limit'])
    output_path = job_spec['build_output_path']
    timeout = job_spec['build_timeout']


    cmd = [
        "/usr/local/bin/nerdctl", "run", "--rm",
        "--name", container_name,                   # unique naming
        "--log-opt", f"max-size={log_size}",        # logging limit
        "--log-opt", "max-file=1",                  # logging limit
        "--runtime", "runsc",                       # Use gVisor
        "--net", "none",                            # Network isolation
        "--volume", f"{workspace_dir}:/workspace",  # bridge between layer 2 & 3
        "--workdir", "/workspace"
    ]

    # add env vars
    if "env" in job_spec:
        for key, value in job_spec['env'].items():
            cmd.extend(["--env", f"{key}={value}"])

    # resource limits (network and read-write allowed at build stage)
    cmd.extend([
        "--cpus", "1", 
        "--memory", f"{memory_limit}m",
        "--pids-limit", "100",
        "timeout", f"{timeout}s",
    ])

    print(f"[nsrunner DEBUG] stage: Build | job_spec payload keys: {list(job_spec.keys())}")
    print(f"[nsrunner DEBUG] stage: Build | value of has_file: {job_spec.get('has_file')}"
          f" (Type: {type(job_spec.get('has_file'))})")

    if job_spec.get('has_file'):

        log_event(job_id, "[nsrunner] downloading workspace from object storage...")
        download_and_extract_workspace(storage_client=storage, job_id=job_id, workspace_dir=workspace_dir)

        # mount the directory and set it as the working directory inside the container
        log_event(job_id, f"[nsrunner]  Files extracted: {os.listdir(workspace_dir)}")
        cmd.extend(["-v", f"{workspace_dir}:/workspace", "-w", "/workspace"])

    cmd.append(job_spec['build_image'])
    cmd.extend(["sh", "-c", job_spec.get('build_command')])

    return cmd


def ns_run_stage_cmd(container_name, job_spec, workspace_dir):
    
    print('Building run stage command for nerdctl')
    
    job_id = job_spec['job_id']
    log_size = job_spec['build_log_size']
    memory_limit = str(job_spec['run_memory_limit'])
    timeout = job_spec['run_timeout']

    cmd = [
        "/usr/local/bin/nerdctl", "run", "--rm",
        "--name", container_name,                   # unique naming
        "--log-opt", f"max-size={log_size}",        # logging limit
        "--log-opt", "max-file=1",                  # logging limit
        "--runtime", "runsc",                       # Use gVisor
        "--volume", f"{workspace_dir}:/workspace",
        "--workdir", "/workspace"
    ]

    # resource limits
    cmd.extend([
        "--cpus", "1", 
        "--memory", f"{memory_limit}m",
        "--pids-limit", "100", 
        "--net", "none",                            # no network access at run stage
        "--read-only",                              # read only fs for run stage
        "timeout", f"{timeout}s",
    ])

    print(f"[nsrunner DEBUG] stage RUN | job_spec payload keys: {list(job_spec.keys())}")

    cmd.append(job_spec['run_image'])
    cmd.extend(["sh", "-c", job_spec.get('run_command')])

    return cmd
        