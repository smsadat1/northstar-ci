from datetime import datetime, timezone
import itertools
import json
import yaml

def parse_yaml_to_json(yaml_file):
    
    json_payload = {
        "version": "1.0",
        "submitted_at": "",        # To be assigned
        "target_file": "",         # To be assigned
        "job": {
            "stages": {
                "build": {
                    "runtime": [],
                    "command": [],
                    "output": "/tmp/build/app",
                    "environment": {},
                    "limits": {
                        "timeout_seconds": 300,
                        "memory_mb": 512,
                        "max_stdout_kb": 512
                    }
                },
                "run": {
                    "runtime": [],
                    "command": [],
                    "limits": {
                        "timeout_seconds": 300,
                        "memory_mb": 512,
                        "max_stdout_kb": 512
                    }
                }
            }
        }
    }

    yaml_template_content = """

        version: "1.0"

        target_file: hudai/

        matrix:
          go_version: [go-1.21, go-1.22]
          db_driver: [postgres, mysql]
          image: [alpine, debian]

        job:
          stages:
            - build:
                runtime: "{go_version}"
                environment:
                  GOCACHE: "/tmp/gocache"
                  ENV: "DEV"
                command: "go build -tags {db_driver} -o /tmp/build/app hudai/"
                output: "/tmp/build/app"
                limits:
                  timeout_seconds: 200
                  memory_mb: 128

            - run:
                runtime: "{image}"
                command: "/tmp/build/app"
                limits:
                  timeout_seconds: 720
                  memory_mb: 1024
                  max_stdout_kb: 10240

    """

    data = yaml.safe_load(yaml_template_content)
    matrix_cfg = data.get("matrix", {})

    # generate all unique combos
    keys, values = zip(*matrix_cfg.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    # extract stages
    stages_list = data.get('job', {}).get('stages', [])
    build_stage = next((s['build'] for s in stages_list if 'build' in s), {})
    run_stage = next((s['run'] for s in stages_list if 'run' in s), {})
    build_limits = build_stage.get("limits", {})
    run_limits = run_stage.get("limits", {})

    # unroll matrix directly into strict JSON parallel arrays
    final_build_runtimes = []
    final_run_runtime = []
    final_commands = []

    for combo in combinations:
        # Use python's native string formatting to inject the values
        build_runtime = build_stage.get("runtime", "")
        build_command = build_stage.get("command", "")
        run_runtime = run_stage.get("runtime", "")
    
        final_build_runtimes.append(build_runtime.format(**combo))
        final_commands.append(build_command.format(**combo))    
        final_run_runtime.append(run_runtime.format(**combo))

    version = data.get('version')
    submitted_at = str(datetime.now(tz=timezone.utc))
    target_file = data.get('target_file')

    json_payload['version'] = version
    json_payload['submitted_at'] = submitted_at
    json_payload['target_file'] = target_file

    # Safely assign your parsed and list-promoted arrays
    json_payload["job"]["stages"]["build"]["runtime"] = final_build_runtimes
    json_payload["job"]["stages"]["build"]["command"] = final_commands
    json_payload["job"]["stages"]["build"]["output"]  = build_stage.get("output")
    json_payload["job"]["stages"]["build"]["environment"]  = build_stage.get("environment")
    json_payload["job"]["stages"]["build"]["limits"]  = build_limits

    # Assigning run stage items directly
    json_payload["job"]["stages"]["run"]["runtime"] = final_run_runtime
    json_payload["job"]["stages"]["run"]["command"] = run_stage.get("output")
    json_payload["job"]["stages"]["run"]["limits"]  = run_limits

    return json_payload

    