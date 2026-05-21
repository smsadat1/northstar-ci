from pydantic import BaseModel

class NSJobSpecSchema(BaseModel):

    # system
    job_id: str 
    runner_id: str

    # command level
    build_command: list[str]
    build_image: list[str]
    build_output_path: list[str]
    run_command: list[str]
    run_image: list[str]

    # resource enforments
    build_timeout: int
    build_memory_limit: int 
    build_log_size: int
    run_timeout: int
    run_memory_limit: int 
    run_log_size: int
    
    # params
    status: str
    has_file: bool
    env: dict[str, str]
    src_url: str