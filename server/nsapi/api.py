import asyncio
import os
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException

from shared.config import message_broker, async_r
from shared.logger import log_event

from s3client import generate_presigned_s3_url
from utils import ns_job_specs
from validator import NSAPIContract


load_dotenv()
app = FastAPI()

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "MINIO_BUCKET")

@app.post('/jobs/run')
def send_job(job_metadata: NSAPIContract):
    try:
        jobspec = ns_job_specs(job_metadata)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job_spec JSON format structure.")

    upload_url = None
    log_event(job_id=jobspec.job_id, message=f"[nsserver] Job ID: {jobspec.job_id}")

    if jobspec.has_file:
        object_key = f"workspaces/{jobspec.job_id}.tar.gz"

        upload_url = generate_presigned_s3_url(
            job_id=jobspec.job_id,
            bucket_name=MINIO_BUCKET, object_name=object_key, expiration=300
        )

        print(f'URL backend wants for s3: {upload_url}')

        if not upload_url:
            raise HTTPException(status_code=500, detail="Failed to initialize storage link")
    
    message_broker.push_job(queue_name="job_queue", payload=jobspec.model_dump())
    log_event(job_id=jobspec.job_id, message="[nsserver] Queued job...")

    return {"job_id": jobspec.job_id, "s3_upload_url": upload_url}
    
    
@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()

    pubsub = async_r.pubsub()
    await pubsub.subscribe(f"channel:{job_id}")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            if message:
                data = message["data"]

                await websocket.send_text(data)

                if data == "END":
                    break

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("Client disconnected")

    finally:
        await pubsub.unsubscribe(f"channel:{job_id}")
        await pubsub.close()
        await websocket.close(code=1000)
    

    