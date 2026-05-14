import redis
from redis import asyncio as aioredis

REDIS_URL = "redis://redis:6379/0"

sync_r = redis.from_url(REDIS_URL, decode_responses=True)
async_r = aioredis.from_url(REDIS_URL, decode_responses=True)