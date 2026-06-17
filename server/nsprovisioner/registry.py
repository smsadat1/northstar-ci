# NSRRT (nsrunner registry table)
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from cache import sync_r
from scheduler import get_nsrunner_instance


class NSRRT_Schema(BaseModel):
    
    # identity
    owner_id: str
    runner_id: str
    runner_ip: str 
    region: str

    # system
    cpu_percent: float
    mem_percent: float
    disk_percent: float

    # control plane metadata
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NSRRT_redis:
    def __init__(self):
        self.r = sync_r

    def upsert_nsrrt(self, owner_id: str,  entry: NSRRT_Schema):
        key = f'nsrrt:{owner_id}'
        
        self.r.hset(key, mapping={
            "owner_id": entry.owner_id,
            "runner_id": entry.runner_id,
            "runner_ip": entry.runner_ip,
            "region": entry.region,
            
            "cpu_percent": entry.cpu_percent,
            "mem_percent": entry.mem_percent,
            "disk_percent": entry.disk_percent,

            "last_heartbeat": entry.last_seen,
        })
        # auto expires if nsrunner instance doesn't ping for more than a minute
        self.r.expire(key, 60)

    def get_associated_runner(self, owner_id: str):
        runner_id = get_nsrunner_instance(owner_id)
        return runner_id

nsrrt = NSRRT_redis()