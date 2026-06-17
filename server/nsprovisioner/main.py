import asyncio, json, logging, time, multiprocessing

from grpcserver import server

from shared.config import NS_RedisProvider, sync_r
from shared.logger import log_event


message_broker = NS_RedisProvider()

# master process coordinator loop (self healing)
if __name__ == "__main__":
    server()