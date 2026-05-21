from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# resource profile
class ResourceLimits(BaseModel):
    timeout_seconds: Optional[int] = Field(default=120, gt=1, le=600)
    memory_mb: Optional[int] = Field(default=512, gt=64, le=4096)
    max_stdout_kb: Optional[int] = Field(default=512, ge=10, le=5120)

# build stage profile
class BuildStage(BaseModel):
    runtime: List[str] = Field(..., min_length=1, max_length=5)
    command: List[str] = Field(..., min_length=1, max_length=5)   
    output: List[str] = Field(..., min_length=1, max_length=5)
    environment: Dict[str, str] = Field(default_factory=dict)
    limits: ResourceLimits

# execution profile
class RunStage(BaseModel):
    runtime: List[str] = Field(..., min_length=1, max_length=5)
    command: List[str] = Field(..., min_length=1, max_length=5)
    limits: ResourceLimits

class PipelineStages(BaseModel):
    build: BuildStage
    run: RunStage

class JobBlueprint(BaseModel):
    stages: PipelineStages

# root request frame
class NSAPIContract(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+$")
    pipeline_id: str = Field(..., pattern=r"^[\w-]+$")
    submitted_at: datetime
    target_file: str = Field(..., pattern=r"^[\w\-./]+$")
    job: JobBlueprint