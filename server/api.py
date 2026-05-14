import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from cache import async_r
from logger import log_event
from dispatcher import generate_job_id
from runner import ns_runner


app = FastAPI()

class Job(BaseModel):
    command: str

@app.post('/jobs/run')
def send_job(job: Job):

    job_id = generate_job_id()
    job_data = {"job_id": job_id, "command": job.command}
    ns_runner.delay(job_data=job_data)

    log_event(job_id=job_id, message="[nsserver] queued job...")
    job_status = {"job_id": job_id, "message": "[nsserver] queued job..."}
    return job_status
    
    
@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()

    history = await async_r.lrange(f"logs:{job_id}", 0, -1)
    for line in history:
        await websocket.send_text(line)

    pubsub = async_r.pubsub()
    await pubsub.subscribe(f"channel:{job_id}")

    async with async_r.pubsub() as pubsub:
        await pubsub.subscribe(f"channel:{job_id}")
        try:
            async for message in pubsub.listen():
            # Check for new messages in Pub/Sub
                if message["type"] == "message":
                    # message['data'] is what you want
                    await websocket.send_text(message["data"])
            
        except WebSocketDisconnect:
            pubsub.unsubscribe(f"channel:{job_id}")