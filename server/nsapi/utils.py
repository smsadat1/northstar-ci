import nanoid

from validator import NSAPIContract
from shared.schema import NSJobSpecSchema


def generate_pipeline_id():
    job_id = nanoid.generate(size=12)
    return job_id

def fetch_owner_id():
    return "owner123"


def ns_job_specs(
    contract: NSAPIContract
) -> NSJobSpecSchema:

    timeout_seconds: int = contract.pipeline.limits.timeout_seconds or 600
    memory_mb: int = contract.pipeline.limits.memory_mb or 4
    max_stdout_kb: int = contract.pipeline.limits.max_stdout_kb or 512
    cpu_count: int = contract.pipeline.limits.cpu_count or 2

    job_spec_metada = NSJobSpecSchema(
        
        # system
        owner_id=fetch_owner_id(),
        pipeline_id=generate_pipeline_id(),
        runner_id='',   # nsprovisioner will decide

        # limits
        timeout_seconds=timeout_seconds,
        memory_mb=memory_mb,
        max_stdout_kb=max_stdout_kb,
        cpu_count=cpu_count,

        # stages
        lint_runtimes=contract.pipeline.stages.lint.runtime,
        lint_envs=contract.pipeline.stages.lint.environment,
        lint_commands=contract.pipeline.stages.lint.command,

        build_runtimes=contract.pipeline.stages.build.runtime,
        build_envs=contract.pipeline.stages.build.environment,
        build_commands=contract.pipeline.stages.build.command,

        test_runtimes=contract.pipeline.stages.test.runtime,
        test_envs=contract.pipeline.stages.test.environment,
        test_commands=contract.pipeline.stages.test.command,

        deploy_runtimes=contract.pipeline.stages.deploy.stages.runtime,
        deploy_envs=contract.pipeline.stages.deploy.stages.environment,
        deploy_commands=contract.pipeline.stages.deploy.stages.command,
        deploy_steps=contract.pipeline.stages.deploy.steps,

        # utils
        status='',      # used for status marking at later stages
        # used by nsrunner to decide file downloads
        has_file= contract.target_file is not None, 
        # in case of passed repo url instead of filepath from cli client
        src_url= str(contract.target_url) if contract.target_file is None else '',     
    ) 

    return job_spec_metada