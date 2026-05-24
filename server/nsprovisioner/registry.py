# NSRRT (nsrunner registry table)
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from cache import sync_r
from scheduler import get_nsrunner_instance


class NSRRT_Schema(BaseModel):
    
    # identity
    runner_id: str
    runner_ip: str
    region: str 

    # system
    current_job: str
    queue_len: int
    ema_velocity: float
    backlog_scope: float

    # control plane metadata
    last_heartbeat: datetime = Field(default_factory=datetime.now(timezone.utc))
    is_healthy: bool = True


class NSRRT_redis:
    def __init__(self):
        self.r = sync_r

    def upsert_nsrrt(self, runner_id: str, entry: NSRRT_Schema):
        key = f'nsrrt:runner:{runner_id}'
        
        self.r.hset(key, mapping={
            "runner_id": entry.runner_id,
            "region": entry.region,
            "queue_len": entry.queue_len,
            "ema_velocity": entry.ema_velocity,
            "backlog_scope": entry.backlog_scope,
            "last_heartbeat": entry.last_heartbeat.isoformat(),
            "is_healthy": "1" if entry.is_healthy else "0",
            "assigned_job_id": entry.current_job
        })
        # auto expires if nsrunner instance doesn't ping for more than a minute
        self.r.expire(key, 60)

    def get_healthy_runner(self, region: str):
        runner_id = get_nsrunner_instance(region)
        return runner_id
    

nsrrt = NSRRT_redis()