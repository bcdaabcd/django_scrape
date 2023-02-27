import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dj_scrape.settings')

# 创建celery实例对象
app = Celery(
    "dj_scrape",
    broker='redis://127.0.0.1:6379/1',
    backend='redis://127.0.0.1:6379/2',
)
# 把celery和django进行组合，识别和加载django的配置文件
# 创建celery实例对象
app = Celery('CeleryDjango')
# 加载setting.py中django的配置
app.config_from_object('django.conf:settings', namespace='CELERY')
# 加载任务
app.autodiscover_tasks(["dj_scrape","task",])


