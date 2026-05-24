import os
from dotenv import load_dotenv

from celery import Celery
from celery.schedules import crontab


load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'REDIS_URL')

NS_IMAGE_MANAGER_INTERVAL = 600.0

celery_app = Celery(
    'worker',
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update( imports=['nsrunner.runner'] )

# celery_app.conf.beatschedule = {
#     'prewarm-images-every-5-min': {
#         'task': 'imgmgr.prewarm_images',  
#         'schedule': NS_IMAGE_MANAGER_INTERVAL,              
#         'args': (optionally_pass_args,)
#     },
# }