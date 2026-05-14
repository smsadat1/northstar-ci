from datetime import datetime, timezone

from cache import sync_r


def log_event(job_id, message):
    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
    formatted_msg = f"[{timestamp}] {message}"

    sync_r.rpush(f"logs:{job_id}", formatted_msg)
    sync_r.expire(f"logs:{job_id}", 3600)

    sync_r.publish(f"channel:{job_id}", formatted_msg)