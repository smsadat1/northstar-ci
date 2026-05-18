import nanoid

def generate_job_id():
    job_id = nanoid.generate(size=12)
    return job_id


