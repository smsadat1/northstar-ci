import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from shared.cache import async_r
from shared.config import message_broker
from shared.logger import log_event
from shared.storage import StorageManager
from dispatcher import generate_job_id


app = FastAPI()
storage = StorageManager()


class JobSpec(BaseModel):
    command: str
    image: str
    env: dict[str, str]

@app.post('/jobs/run')
def send_job(
    job_spec_str: str = Form(...),         
    file: UploadFile = File(None)
):

    try:
        job_data = json.loads(job_spec_str)
        jobspec = JobSpec(**job_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job_spec JSON format structure.")

    job_id = generate_job_id()
    log_event(job_id=job_id, message=f"[nsserver] Job ID: {job_id}")

    job_data = {
        "job_id": job_id, 
        "runner_id": "",
        "command": jobspec.command,
        "image": jobspec.image, 
        "env": jobspec.env,
        "status": "PENDING", 
        "has_file": bool(file),
    }

    if file: 
        storage.upload_file(file, f"{job_id}.tar.gz")
        log_event(job_id=job_id, message="[nsserver] Transferring files")
        
    message_broker.push_job(queue_name="job_queue", payload=job_data)

    log_event(job_id=job_id, message="[nsserver] queued job...")
    job_status = {"job_id": job_id}
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