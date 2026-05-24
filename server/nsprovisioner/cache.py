import redis
from redis import asyncio as aioredis

NSPROVISIONER_REDIS = "redis://localhost:6379/0"

async_r = aioredis.from_url(NSPROVISIONER_REDIS, decode_responses=True)
sync_r = redis.from_url(NSPROVISIONER_REDIS, decode_responses=True)
