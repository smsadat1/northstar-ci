import time
from celery.signals import task_prerun, task_postrun, task_success

from envs import (
    ACTIVE_EXECUTION_TIMERS, TASK_ELAPSED_TIME, RUNNER_ID, NODE_CURRENT_EMA_VELOCITY, ALPHA
)
from .telemertry import telemetry_bridge
from shared.config import sync_r


@task_prerun.connect(sender='tasks.nsrunner')
def task_prerun_handler(sender, task_id, task, args, kwargs, **extra):
    """Fires exactly before the container workload starts executing."""
    ACTIVE_EXECUTION_TIMERS[task_id] = time.time()

@task_success.connect(sender='tasks.nsrunner')
def calculate_elapsed_time(sender, result, **extra):
    """Fires immediately upon successful task completion."""
    task_id = sender.request.id
    start_time = ACTIVE_EXECUTION_TIMERS.pop(task_id, None)

    if start_time is not None:
        elapsed_time = time.time() - start_time
        # safeguard against instant 0.0s tasks (Divide-by-zero protection)
        TASK_ELAPSED_TIME[task_id] = max(elapsed_time, 0.0001)
    else:
        # fallback metric if prerun timer failed or dropped
        TASK_ELAPSED_TIME[task_id] = 1.0


@task_postrun.connect(sender='tasks.nsrunner')
def send_metrics(sender, task_id, task, args, kwargs, **extra):

    elapsed_time = TASK_ELAPSED_TIME.pop(task_id, 1.0)
    current_instant_velocity = 1.0 / elapsed_time
    NODE_CURRENT_EMA_VELOCITY = (current_instant_velocity * ALPHA) + (NODE_CURRENT_EMA_VELOCITY * (1 - ALPHA))

    runner_queue = f"queue-{RUNNER_ID}"
    try:
        queue_len = sync_r.llen(runner_queue)
    except Exception:
        queue_len = 0 # Prevent Redis connection hitches from crashing the metric step

    safe_velocity = max(NODE_CURRENT_EMA_VELOCITY, 0.001)
    backlog_scope = queue_len / safe_velocity

    # Dispatch via client outbound gRPC pipeline up to nsprovisioner
    try:
        telemetry_bridge.send(
            runner_id=RUNNER_ID,
            job_id=task_id,
            region='Singapore',
            queue_len=queue_len,
            ema_velocity=safe_velocity,
            backlog_scope=backlog_scope,
        )
    except Exception as e:
        print(f"Telemetry transport dropped frame: {e}")


