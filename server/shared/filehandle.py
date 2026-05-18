import os
import tarfile
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("/tmp/uploads")
EXTRACT_DIR = Path("/tmp/jobs")


def safe_extract(tar, path="."):
    for member in tar.members:
        member_path = os.path.join(path, member.name)

        abs_directory = os.path.abspath(path)
        abs_target = os.path.abspath(member_path)

        if not abs_target.startswith(abs_directory):
            raise Exception("Path traversal detected")

    tar.extractall(path)


def handle_file_upload(file: UploadFile, job_id: str):
    archive_path = UPLOAD_DIR / f"{job_id}.tar.gz"
    extract_path = EXTRACT_DIR / job_id

    extract_path.mkdir(parents=True, exist_ok=True)

    with open(archive_path, "wb") as f:
        while chunk := file.read(1024 * 1024):
            f.write(chunk)

    with tarfile.open(archive_path, "r:gz") as tar:
       safe_extract(tar=tar, path=str(extract_path))

    return extract_path
    