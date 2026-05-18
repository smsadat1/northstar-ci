from pydantic import BaseModel

class JobSpecSchema(BaseModel):
    job_id: str
    runner_id: str
    command: str 
    image: str
    env: dict[str, str]
    status: str
    has_file: bool 
    src_url: str