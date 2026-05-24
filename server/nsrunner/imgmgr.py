# manages and caches images 
# import subprocess

# from envs import ALLOWED_IMAGES
# from shared.worker import celery_app


# @celery_app.task
# def prewarm_images():
#     for name, tag in ALLOWED_IMAGES.items():
#         # check local existence
#         check = subprocess.run(['nerdctl', 'image', 'inspect', tag], capture_output=True)
#         if check.returncode != 0:
#             print(f'Pre warming image: {name}|{tag}')
#             subprocess.run(['nerdctl', 'pull', tag])