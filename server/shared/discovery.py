import json
from .cache import sync_r


def get_healthy_runner(max_load=80):
    
    # Get all heartbeat keys: runner:registry:*
    keys = sync_r.keys("runner:registry:*")

    best_runner = None
    lowest_load = 101

    # find best runner based on lowest load
    for key in keys:
        stats = json.loads(sync_r.get(key))
        if stats['load'] < max_load and stats['load'] < lowest_load:
            lowest_load = stats['load']
            best_runner = stats
            
    return best_runner