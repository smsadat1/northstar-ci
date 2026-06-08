from datetime import datetime, timezone
import itertools
import json
import yaml


def render(obj, variables):
    if isinstance(obj, str):
        return obj.format(**variables)
    if isinstance(obj, dict):
        return {k:render(v, variables) for k, v in obj.items()}
    if isinstance(obj, list):
        return [render(v, variables) for v in obj]

    return obj


def parse_yaml_to_json(yaml_file):
    
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    final_lint_runtimes = []
    final_lint_envs = []
    final_lint_commands = []

    final_build_runtimes = []
    final_build_envs = []
    final_build_commands = []

    final_test_runtimes = []
    final_test_envs = []
    final_test_commands = []

    final_deploy_runtimes = []
    final_deploy_envs = []
    final_deploy_commands = []


    version = data.get('version')
    submitted_at = str(datetime.now(tz=timezone.utc))
    target_file = data.get('target_file')

    # extract stages
    stages_list = data.get('jobs', {}).get('stages', [])
    resource_limits = data.get('jobs', {}).get('limits',[])

    lint_stage = next((s['lint'] for s in stages_list if 'lint' in s), {})
    lint_envs = lint_stage.get("environment", {})

    build_stage = next((s['build'] for s in stages_list if 'build' in s), {})
    build_envs = build_stage.get("environment", {})

    test_stage = next((s['test'] for s in stages_list if 'test' in s), {})
    test_envs = test_stage.get("environment", {})

    deploy_stage = next((s['deploy'] for s in stages_list if 'deploy' in s), {})
    deploy_envs = deploy_stage.get("environment", {})

    # generate all unique combos for matrix build
    matrix_cfg = data.get("matrix", {})

    if matrix_cfg:
        keys, values = zip(*matrix_cfg.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # native str formatting to inject the values
        for combo in combinations:
            rendered_lint = render(lint_stage, combo)
            assert isinstance(rendered_lint, dict)
            final_lint_runtimes.append(rendered_lint['runtime'])
            final_lint_envs.append(rendered_lint.get("environment", {}))
            final_lint_commands.append(rendered_lint["command"])

            rendered_build = render(build_stage, combo)
            assert isinstance(rendered_build, dict)
            final_build_runtimes.append(rendered_build['runtime'])
            final_build_envs.append(rendered_build.get("environment", {}))
            final_build_commands.append(rendered_build["command"])

            rendered_test = render(test_stage, combo)
            assert isinstance(rendered_test, dict)
            final_test_runtimes.append(rendered_test['runtime'])
            final_test_envs.append(rendered_test.get("environment", {}))
            final_test_commands.append(rendered_test["command"])

            rendered_deploy = render(deploy_stage, combo)
            assert isinstance(rendered_deploy, dict)
            final_deploy_runtimes.append(rendered_deploy['runtime'])
            final_deploy_envs.append(rendered_deploy.get("environment", {}))
            final_deploy_commands.append(rendered_deploy["command"])
            

    # wrap single string values in lists to satisfy List[str] even for linear cases
    else:
        l_runtime = lint_stage.get("runtime")
        final_lint_runtimes = [l_runtime] if isinstance(l_runtime, str) else (l_runtime or [])
        l_env = lint_stage.get("environment")
        final_lint_envs = {l_env} if isinstance(l_env, str) else (l_env or {})
        l_command = lint_stage.get("command")
        final_lint_commands = [l_command] if isinstance(l_command, str) else (l_command or [])

        b_runtime = build_stage.get("runtime")
        final_build_runtimes = [b_runtime] if isinstance(b_runtime, str) else (b_runtime or [])
        b_env = build_stage.get("environment")
        final_build_envs = {b_env} if isinstance(b_env, str) else (b_env or {})
        b_command = build_stage.get("command")
        final_build_commands = [b_command] if isinstance(b_command, str) else (b_command or [])

        t_runtime = test_stage.get("runtime")
        final_test_runtimes = [t_runtime] if isinstance(t_runtime, str) else (t_runtime or [])
        t_env = test_stage.get("environment")
        final_test_envs = {t_env} if isinstance(t_env, str) else (t_env or {})
        t_command = test_stage.get("command")
        final_test_commands = [t_command] if isinstance(t_command, str) else (t_command or [])

        d_runtime = deploy_stage.get("runtime")
        final_deploy_runtimes = [d_runtime] if isinstance(d_runtime, str) else (d_runtime or [])
        d_env = deploy_stage.get("environment")
        final_lint_envs = {d_env} if isinstance(d_env, str) else (d_env or {})
        d_command = deploy_stage.get("command")
        final_deploy_commands = [d_command] if isinstance(d_command, str) else (d_command or [])

    # isolate and ensure the run stage command is explicitly wrapped in a list
    # r_command = test_stage.get("command")
    # final_run_commands = [r_command] if isinstance(r_command, str) else (r_command or [])
    

    json_payload =  {
        "version": version,
        "target_file": target_file,
        "submitted_at": submitted_at,

        "job": {
            "limits": resource_limits,
            "stages": {
                "lint": {
                    "runtime": final_lint_runtimes,
                    "environment": final_lint_envs,
                    "command": final_lint_commands,
                },
                "build": {
                    "runtime": final_build_runtimes,
                    "environment": final_build_envs,
                    "command": final_build_commands,
                },
                "test": {
                    "runtime": final_test_runtimes,
                    "environment": final_test_envs,
                    "command": final_test_commands,
                },
                "deploy": {
                    "runtime": final_deploy_runtimes,
                    "environment": final_deploy_envs,
                    "command": final_deploy_commands,
                    "steps": deploy_stage.get("steps") 
                },
            }
        }
    }

    return json_payload
    