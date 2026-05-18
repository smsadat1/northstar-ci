import redis
from redis import asyncio as aioredis

from .messaging import NS_RedisProvider

REDIS_URL = "redis://redis:6379/0"

async_r = aioredis.from_url(REDIS_URL, decode_responses=True)
sync_r = redis.from_url(REDIS_URL, decode_responses=True)

message_broker = NS_RedisProvider(url="redis://redis:6379/0")