import os
import threading

from .heartbeat import send_hearbeat
from shared.worker import celery_app

RUNNER_ID = os.getenv("RUNNER_ID", "runner-123")


if __name__ == "__main__":

    t = threading.Thread(target=send_hearbeat, daemon=True)
    t.start()

    print(f"[nsrunner] Instantiating Celery Worker object programmatically...")
    
    # 2. Boot the worker object directly bypassing command-line string parsing
    worker = celery_app.Worker(
        queues=[f'queue-{RUNNER_ID}'],
        loglevel='INFO',
        optimization='fair' # Recommended for isolated job execution
    )
    
    # 3. Start the worker loop. This blocks the main thread permanently.
    worker.start()