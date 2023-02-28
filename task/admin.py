from django.contrib import admin
from task.models import TaskCategory
# Register your models here.

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name']


    