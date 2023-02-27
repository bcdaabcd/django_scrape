from django.urls import path
from . import views

urlpatterns = [
    path('',views.task_list,name='task_list'),
    path('category/<int:category_id>',views.task_with_category,name='task_with_category'),

    path('change_task_status',views.change_task_status,name='change_task_status'),
    path('start_or_stop_all',views.start_or_stop_all,name='start_or_stop_all'),
    path('tast_info_edit',views.task_info_edit,name='task_info_edit'),
    
]
