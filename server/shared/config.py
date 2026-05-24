import os
from dotenv import load_dotenv

import redis
from redis import asyncio as aioredis

from .messaging import NS_RedisProvider

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'REDIS_URL')


async_r = aioredis.from_url(REDIS_URL, decode_responses=True)
sync_r = redis.from_url(REDIS_URL, decode_responses=True)

message_broker = NS_RedisProvider(url="redis://redis:6379/0")