# builds the cmd 

def build_nerdctl_cmd(runner_id, job_spec):
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

    cmd.append(job_spec["image"])
    cmd.extend(["/bin/sh", "-c",  job_spec["command"]])

    return cmd
        