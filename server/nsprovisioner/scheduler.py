import json
import logging

from cache import sync_r


# uses greedy scheduling to get runner for task
def get_nsrunner_instance(target_region: str, healthy_threshold: float = 15.55):
    """
    Scans the Redis NSRRT registry, evaluates live metrics via a weighted 
    cost formula, and selects the optimal available runner instance.
    """
    best_runner_id = None
    target_region = 'Singapore'
    lowest_system_load = float('inf')

    for runner_key in sync_r.scan_iter("nsrrt:runner:*"):
        runner_data = sync_r.hgetall(runner_key)

        if runner_data.get('is_healthy') != '1':
            # skip unhealthy runners
            continue
        
        # not needed now
        if runner_data.get("region") != target_region:
            continue

        try: 
            queue_len = int(runner_data.get('queue_len'))
            ema_velocity = float(runner_data.get('ema_velocity'))
            backlog_scope = float(runner_data.get('backlog_scope'))
            runner_id = runner_data.get("runner_id")
        except (ValueError, TypeError) as e:
            logging.error(f"[Scheduler] Corrupted metric data for key {runner_key}: {e}")
            continue

        
        system_load = (queue_len * 0.3) + (ema_velocity * 0.2) + (backlog_scope * 0.1)

        if system_load > healthy_threshold: 
            is_healthy = False 
            continue

        # greedy selection: find the runner with the MOST available breathing room
        if system_load < lowest_system_load:
            lowest_system_load = system_load
            best_runner_id = runner_id

    # returns the absolute best runner, or None if the entire cluster is red-lined
    return best_runner_id
