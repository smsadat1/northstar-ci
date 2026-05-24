import socket

RUNNER_ID = socket.gethostname()

ALLOWED_IMAGES = {
    "python": "python:3.11-slim",
    "node": "node:20-alpine",
    "bash": "alpine:latest"
}

# in memory dict
ACTIVE_EXECUTION_TIMERS = {}
PREV_EMA_VALUE = {}
TASK_ELAPSED_TIME = {}
TELEMETRY_BUFFER = {}

NS_CI_JOB_TIMEOUT = 300
MAX_LINES = 50000

ALPHA = 0.2
NODE_CURRENT_EMA_VELOCITY = 1.0  # Safe initial baseline seed (1 task/sec)
