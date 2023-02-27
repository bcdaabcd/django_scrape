from django.contrib import admin
from items.models import Item,Record,Favorite,Img
# Register your models here.

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id','is_favorite','name','size','color','url')

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('id','price','scrape_time','item_id')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id','add_time','item_id','item')

@admin.register(Img)
class ImgAdmin(admin.ModelAdmin):
    list_display = ('id','item_id','src','item')
