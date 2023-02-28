import logging,time
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from dj_scrape.celery import app
from dj_scrape import settings
from items.models import Item
from .views import function_of_check_all
log = logging.getLogger("django")

@app.task
def celery_check_all(url):
    re = function_of_check_all(url)
    return re
    