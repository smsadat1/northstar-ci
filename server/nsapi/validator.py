from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, FilePath, AnyUrl, model_validator


# resource profile
class ResourceLimits(BaseModel):
    timeout_seconds: Optional[int] = Field(default=120, gt=1, le=600)
    memory_mb: Optional[int] = Field(default=512, gt=64, le=4096)
    max_stdout_kb: Optional[int] = Field(default=512, ge=10, le=5120)
    cpu_count: Optional[int] = Field(default=2, ge=64, le=1)

# CI stage profile
class StageModel(BaseModel):
    runtime: List[str] = Field(..., min_length=1, max_length=5)
    environment: Dict[str, str] = Field(default_factory=dict)
    command: List[str] = Field(..., min_length=1, max_length=5)   

# deploy stage
class DeployStageModel(BaseModel):
    stages: StageModel
    steps: list[str]

class PipelineStages(BaseModel):
    lint: StageModel
    build: StageModel
    test: StageModel
    deploy: DeployStageModel

class PipelineBlueprint(BaseModel):
    limits: ResourceLimits
    stages: PipelineStages

# root request frame
class NSAPIContract(BaseModel):
    version: str = Field(..., pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)([ab])?$")
    target_file: Optional[FilePath] = None
    target_url: Optional[AnyUrl] = None
    submitted_at: datetime
    pipeline: PipelineBlueprint

    @model_validator(mode='after')
    def check_either(self):
        if self.target_file is None and self.target_url is None:
            raise ValueError("Either target_file or target_url must be provided")
        return self