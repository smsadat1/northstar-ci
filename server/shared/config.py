from .messaging import NS_RedisProvider

message_broker = NS_RedisProvider(url="redis://redis:6379/0")