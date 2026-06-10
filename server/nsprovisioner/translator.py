# translate NSJobSpecSchema to NSRunnerJobSpec
# NSRunnerJobSpec is the raw assembly like instruction for nsrunner
from itertools import product

from shared.schema import NSJobSpecSchema, NSRunnerJobSpec


def expand_job_spec(job_spec_data: NSJobSpecSchema) -> list[NSRunnerJobSpec]:

    #  validate and convert the raw dict into Pydantic object
    if isinstance(job_spec_data, dict):
        job_spec = NSJobSpecSchema(**job_spec_data)
    else:
        job_spec = job_spec_data

    expanded_specs: list[NSRunnerJobSpec] = []

    combinations = product(
        job_spec.lint_commands,
        job_spec.lint_runtimes,
        job_spec.build_commands,
        job_spec.build_runtimes,
        job_spec.test_runtimes,
        job_spec.test_commands,
    )

    task_counter = 1


    for(
        lint_command, lint_runtime, build_command, build_runtime, test_command, test_runtime
    ) in combinations:
        expanded_specs.append(
           NSRunnerJobSpec(
                pipeline_id=job_spec.pipeline_id,
                task_id=job_spec.pipeline_id + '_' + str(task_counter),

                timeout_seconds=job_spec.timeout_seconds,
                memory_mb=job_spec.memory_mb,
                max_stdout_kb=job_spec.max_stdout_kb,
                cpu_count=job_spec.cpu_count,

                lint_runtime=lint_runtime,
                lint_envs=job_spec.lint_envs,
                lint_command=lint_command,
                build_command=build_command,
                build_envs=job_spec.build_envs,
                build_runtime=build_runtime,
                test_command=test_command,
                test_envs=job_spec.test_envs,
                test_runtime=test_runtime,
               
                status=job_spec.status,
                has_file=job_spec.has_file,
                src_url=job_spec.src_url,
           )
        )      
        task_counter += 1

    return expanded_specs  
