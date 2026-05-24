import asyncio
import logging
from typing import Optional

from shared.rpc import coordinator_pb2 


logger = logging.getLogger(__name__)


class TelemetryBridge:
    def __init__(self, max_buffer_size: int = 100):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._buffer: Optional[asyncio.Queue] = None
        self._max_buff_size = max_buffer_size

    def register_loop(self, loop: asyncio.AbstractEventLoop):
        """Captures the active async event loop and instantiates the Queue within it."""
        self._loop = loop
        # asyncio.Queue created inside the running loop context
        self._buffer = asyncio.Queue(maxsize=self._max_buff_size)
        logger.info("Telemetry bridge successfully bound to async event loop.")

    def get_buffer(self) -> asyncio.Queue:
        """Returns the internal queue instance for the async worker loop."""
        if self._buffer is None:
            raise RuntimeError("Telemetry bridge buffer accessed before loop registration!")
        return self._buffer
    
    def send(self, runner_id: str, job_id: str, region: str, queue_len: int, ema_velocity: float, backlog_scope: float):
        """ 
        The thread-safe middleman function used between Celery and gRPC 
        """

        if not self._loop or not self._loop.is_running() or self._buffer is None:
            logger.warning("⚠️ Drop Frame: Telemetry bridge is offline or loop not running yet.")
            return

        # package raw metric data into compiled gRPC message model
        heartbeat_frame = coordinator_pb2.NSTelemetryHeartBeat(
            runner_id=runner_id,
            current_job_id=job_id,
            region=region,
            queue_len=int(queue_len),
            ema_velocity=float(ema_velocity),
            backlog_scope=float(backlog_scope)
        )

        # thread-safely inject the frame straight into the async loop queue
        self._loop.call_soon_threadsafe(self._buffer.put_nowait, heartbeat_frame)


telemetry_bridge = TelemetryBridge()

