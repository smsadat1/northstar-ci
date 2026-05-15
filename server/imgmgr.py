# manages and caches images 
import subprocess

from worker import celery_app

ALLOWED_IMAGES = {
    "python": "python:3.11-slim",
    "node": "node:20-alpine",
    "bash": "alpine:latest"
}

@celery_app.task
def prewarm_images():
    for name, tag in ALLOWED_IMAGES.items():
        # check local existence
        check = subprocess.run(['nerdctl', 'image', 'inspect', tag], capture_output=True)
        if check.returncode != 0:
            print(f'Pre warming image: {name}|{tag}')
            subprocess.run(['nerdctl', 'pull', tag])