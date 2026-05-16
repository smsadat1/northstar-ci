from datetime import datetime, timezone

from .cache import sync_r


def log_event(job_id, message, exec_logs: bool = False):

    send_mesg = ''

    if exec_logs:
        send_mesg = message
    else:
        timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
        formatted_msg = f"[{timestamp}] {message}"
        send_mesg = formatted_msg

    sync_r.rpush(f"logs:{job_id}", send_mesg)
    sync_r.expire(f"logs:{job_id}", 3600)

    sync_r.publish(f"channel:{job_id}", send_mesg)