from pydantic import BaseModel

# internal job_spec passed from nsapi to nsprovisioner
class NSJobSpecSchema(BaseModel):
    # system
    owner_id: str
    pipeline_id: str 
    runner_id: str 

    # limits
    timeout_seconds: int
    memory_mb: int
    max_stdout_kb: int
    cpu_count: int

    # stages
    lint_runtimes: list[str]
    lint_envs: dict[str, str]
    lint_commands: list[str]

    build_runtimes: list[str]
    build_envs: dict[str, str]
    build_commands: list[str]

    test_runtimes: list[str]
    test_envs: dict[str, str]
    test_commands: list[str]

    deploy_runtimes: list[str]
    deploy_envs: dict[str, str]
    deploy_commands: list[str]
    deploy_steps: list[str]

    # utils
    status: str
    has_file: bool
    src_url: str


# final job_spec after job_spec expansion by nsprovisioner
class NSRunnerJobSpec(BaseModel):
    # system
    pipeline_id: str 
    task_id: str

    # resource enforments
    timeout_seconds: int
    memory_mb: int
    max_stdout_kb: int
    cpu_count: int
    
    # stages
    lint_runtime: str 
    lint_envs: dict[str, str]
    lint_command: str

    build_runtime: str 
    build_envs: dict[str, str]
    build_command: str 
    
    test_runtime: str 
    test_envs: dict[str, str]
    test_command: str
    
    # params
    status: str
    has_file: bool
    src_url: str