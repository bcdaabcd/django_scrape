from django.db import models
from items.models import Item
from django.contrib.contenttypes.models import ContentType

class TaskCategory(models.Model):
    content_type = models.OneToOneField(ContentType,on_delete=models.DO_NOTHING)



