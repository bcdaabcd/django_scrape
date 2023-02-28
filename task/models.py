from django.db import models
from items.models import Item
from django.contrib.contenttypes.models import ContentType

class TaskCategory(models.Model):
    name = models.CharField(max_length=30,default=None)


