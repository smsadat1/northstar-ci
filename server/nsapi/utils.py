import nanoid

from validator import NSAPIContract
from shared.schema import NSJobSpecSchema


def generate_job_id():
    job_id = nanoid.generate(size=12)
    return job_id


def ns_job_specs(
    contract: NSAPIContract
) -> NSJobSpecSchema:

    b_timeout = contract.job.stages.build.limits.timeout_seconds
    b_memory = contract.job.stages.build.limits.memory_mb
    b_stdout_size = contract.job.stages.build.limits.max_stdout_kb
    r_timeout = contract.job.stages.run.limits.timeout_seconds
    r_memory = contract.job.stages.run.limits.memory_mb
    r_stdout_size = contract.job.stages.run.limits.max_stdout_kb

    job_spec_metada = NSJobSpecSchema(
        
        # system
        job_id=generate_job_id(),
        runner_id='',   # nsprovisioner will decide

        # commands level
        build_command=contract.job.stages.build.command,
        build_image=contract.job.stages.build.runtime,
        build_output_path=contract.job.stages.build.output,
        run_command=contract.job.stages.run.command,
        run_image=contract.job.stages.run.runtime,
        
        # resource limits enforcements
        build_timeout= b_timeout or 600,
        build_memory_limit= b_memory or 512,
        build_log_size= b_stdout_size or 512,
        run_timeout= r_timeout or 600,
        run_memory_limit= r_memory or 512,
        run_log_size= r_stdout_size or 512,

        env=contract.job.stages.build.environment,
        status='',
        has_file= contract.target_file is not None,
        src_url='',
    ) 

    return job_spec_metada