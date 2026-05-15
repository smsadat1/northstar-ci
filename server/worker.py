from celery import Celery
from celery.schedules import crontab


NS_IMAGE_MANAGER_INTERVAL = 600.0

celery_app = Celery(
    'worker',
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery_app.conf.update( imports=['runner'] )

celery_app.conf.beatschedule = {
    'prewarm-images-every-5-min': {
        'task': 'imgmgr.prewarm_images',  
        'schedule': NS_IMAGE_MANAGER_INTERVAL,              
        # 'args': (optionally_pass_args,)
    },
}