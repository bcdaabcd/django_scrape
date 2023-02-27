from django.db import models
from django.db.models import Count

# Create your models here.
class Record(models.Model):
    item = models.ForeignKey('Item',on_delete=models.CASCADE)
    price = models.IntegerField()
    scrape_time = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"record of {self.item.name}"

class Img(models.Model):
    item = models.ForeignKey('Item',on_delete=models.CASCADE)
    src = models.CharField(max_length=255)

class Favorite(models.Model):
    item=models.OneToOneField('Item',on_delete=models.CASCADE)
    add_time=models.DateTimeField(auto_now_add=True)

class Item(models.Model):
    name = models.CharField(max_length=300)
    is_favorite = models.BooleanField(default=False)
    size = models.CharField(max_length=50,null=True,default=None,blank=True)
    color = models.CharField(max_length=30,null=True,default=None,blank=True)
    url = models.CharField(max_length=500,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['-id']



