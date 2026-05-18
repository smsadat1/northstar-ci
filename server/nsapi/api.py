import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from shared.config import message_broker, async_r
from shared.logger import log_event
from shared.schema import JobSpecSchema
from shared.storage import StorageManager

from s3client import generate_presigned_s3_url
from utils import generate_job_id


app = FastAPI()
storage = StorageManager()

class JobSpec(BaseModel):
    command: str
    image: str
    has_file: bool
    env: dict[str, str]

@app.post('/jobs/run')
def send_job(job_spec_str: str = Form(...)):
    try:
        job_data = json.loads(job_spec_str)
        jobspec = JobSpec(**job_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job_spec JSON format structure.")

    job_id = generate_job_id()
    log_event(job_id=job_id, message=f"[nsserver] Job ID: {job_id}")

    job_data = JobSpecSchema(
        job_id=job_id,
        runner_id='',
        command=jobspec.command,
        has_file=jobspec.has_file,
        image = jobspec.image,
        env = jobspec.env,
        status = "PENDING",
        src_url='',
    )

    if jobspec.has_file:
        bucket = "ns-storage-bucket"
        object_key = f"workspaces/{job_id}.tar.gz"

        upload_url = generate_presigned_s3_url(
            bucket_name=bucket, object_name=object_key, expiration=300
        )

        if not upload_url:
            raise HTTPException(status_code=500, detail="Failed to initialize storage link")
    
    message_broker.push_job(queue_name="job_queue", payload=job_data.model_dump())
    log_event(job_id=job_id, message="[nsserver] Queued job...")

    return {"job_id": job_id, "s3_upload_url": upload_url}
    
    
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