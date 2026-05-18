import os
import time
import tarfile


def download_and_extract_workspace(storage_client, job_id, workspace_dir):

    local_zip = f"/tmp/{job_id}.tar.gz"
    
    # Retry Configuration
    max_attempts = 5
    base_delay = 2 # Starts at 2 seconds

    for attempt in range(1, max_attempts + 1):
        print(f"[nsrunner] Attempting download for job {job_id} (Try {attempt}/{max_attempts})...")
    
        success = storage_client.download_file(f"workspaces/{job_id}.tar.gz", local_zip)
        
        if success:
            print(f"[nsrunner] Workspace asset acquired successfully on attempt {attempt}.")
            break # Exit the retry loop safely
            
        # If success is False, handle backoff and retries manually
        print(f"[nsrunner] Download attempt {attempt} failed (Asset missing or MinIO/S3 replication lag).")

        if attempt == max_attempts:
            print(f"[nsrunner] CRITICAL: Workspace download failed permanently after {max_attempts} attempts.")
            return False

        # Exponential backoff calculation (2s, 4s, 8s, 16s...)
        delay = base_delay * (2 ** (attempt - 1))
        print(f"[nsrunner] Sleeping for {delay}s before retrying...")
        time.sleep(delay)

    # Proceed to extraction safely
    try:
        print(f"[nsrunner] Extracting archive {local_zip} into workspace folder {workspace_dir}...")
        with tarfile.open(local_zip, "r:gz") as tar:
            tar.extractall(path=workspace_dir)
            
        # Clean up the compressed download file to keep /tmp clear
        if os.path.exists(local_zip):
            os.remove(local_zip)
            
        print(f"[nsrunner] Job environment ready inside {workspace_dir}")
        return True
        
    except Exception as e:
        print(f"[nsrunner] Critical error during extraction: {e}")
        return False