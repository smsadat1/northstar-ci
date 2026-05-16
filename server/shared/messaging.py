from abc import ABC, abstractmethod
import json
import redis


class NS_MessageProvider(ABC):

    @abstractmethod
    def publish_log(self, job_id: str, message: str):
        pass

    @abstractmethod
    def push_job(self, queue_name: str, payload: dict):
        pass

    @abstractmethod
    def pop_job(self, queue_name: str, timeout: int = 2) -> dict | None:
        """Blocks for 'timeout' seconds. Returns the parsed dict or None if empty."""
        pass

    # @abstractmethod
    # def subscribe_logs(self, job_id: str):
    #     """Used by the API/CLI to listen for logs"""
    #     pass


class NS_RedisProvider(NS_MessageProvider):

    def __init__(self, url="redis://redis:6379/0"):
        self.r = redis.from_url(url=url, decode_responses=True)

    def publish_log(self, job_id, message):
        # Pub/Sub for real-time log streaming
        self.r.publish(f"logs:{job_id}", message)

    def push_job(self, queue_name, payload):
        # LPUSH for job queueing
        self.r.lpush(queue_name, json.dumps(payload))

    def pop_job(self, queue_name, timeout=2):
        # BRPOP returns a tuple: (queue_name, item_string) if found, or None if timed out
        result = self.r.brpop(queue_name, timeout=timeout)
        
        if result is None:
            return None
            
        # unpack the tuple (only care about the item string payload)
        _, item_str = result
        try:
            return json.loads(item_str)
        except (json.JSONDecodeError, TypeError):
            print(f"[Provider] Error: Corrupted job string in queue: {item_str}")
            return None