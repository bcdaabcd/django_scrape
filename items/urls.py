from django.urls import path
from . import views
from . import tasks

urlpatterns = [
    path('',views.item_list,name='item_list'),
    path('<int:item_id>',views.item_detail,name='item_detail'),
    path('favorite/',views.favorite_list,name='favorite_list'),

    path('fav_add/',views.fav_add,name='fav_add'),
    path('check_all/',views.check_all,name='check_all'),
    path('merge_same_record',views.merge_same_record,name='merge_same_record'),
]
