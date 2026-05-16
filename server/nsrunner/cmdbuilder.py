# builds the cmd
import os 
import shutil
import tarfile

from shared.logger import log_event
from shared.storage import StorageManager

storage = StorageManager()


def build_nerdctl_cmd(runner_id, job_spec, workspace_dir):
    
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

    if job_spec.get('has_file'):
        log_event(job_id, "[nsrunner] downloading workspace from object storage...")
        
        local_zip = f"/tmp/{job_id}.tar.gz"
        success = storage.download_file(f"{job_id}.tar.gz", local_zip)
        
        if not success:
            log_event(job_id, "[nsrunner] CRITICAL: Workspace download failed! Halting execution")
            return

        # safely extract the archive on the host machine
        os.makedirs(workspace_dir, exist_ok=True)
        try:
            with tarfile.open(local_zip, "r:gz") as tar:
                tar.extractall(path=workspace_dir)
            log_event(job_id, "[nsrunner] Workspace unpacked successfully.")
        except Exception as e:
            log_event(job_id, f"[nsrunner] CRITICAL: Extraction failed: {str(e)}")
            return
        finally:
            # Clean up the raw zip immediately to save space
            if os.path.exists(local_zip):
                os.remove(local_zip)

        # mount the directory and set it as the working directory inside the container
        # Note: Even with --read-only rootfs, mounted volumes remain writable unless specified as :ro
        cmd.extend(["-v", f"{workspace_dir}:/workspace", "-w", "/workspace"])

    cmd.append(job_spec["image"])
    cmd.extend(["/bin/sh", "-c",  job_spec["command"]])

    return cmd
        