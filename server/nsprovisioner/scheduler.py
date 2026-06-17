from cache import sync_r


# uses greedy scheduling to get runner for task
def get_nsrunner_instance(owner_id: str, healthy_threshold: float = 15.55):
    """
    Scans the Redis NSRRT registry, evaluates live metrics via a weighted 
    cost formula, and selects the optimal available runner instance.
    """
    # lowest_system_load = float('inf')

    # find all nsrunner instances under speicified owner 
    # one owner has only one nsrunner instance for now
    for runner_key in sync_r.scan_iter(f"nsrrt:{owner_id}:*"):
        runner_data = sync_r.hgetall(runner_key)
        runner_id = runner_data.get('runner_id')
        runner_ip = runner_data.get('runner_ip')

    return runner_id, runner_ip


