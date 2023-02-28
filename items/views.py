import time,multiprocessing,random
from django_celery_beat.models import PeriodicTask
from django.shortcuts import get_object_or_404,render,redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Count,Max,Min,Window
from django.db.models.functions import DenseRank
from django.http import JsonResponse
from django.db.utils import IntegrityError
from django.contrib import messages
from django.core import exceptions
from django.conf import settings
from .models import Item,Record,Favorite
from dj_scrape.utils import get_certain_item_info,save_item_or_add_record_on_exist_item

def item_list_common_data(request,all_item_list):
    context = {}
# 分页
    paginator = Paginator(all_item_list,settings.EACH_PAGE_OBJ_NUM)
    page_num = request.GET.get('page',1)
    cur_page = paginator.get_page(page_num)
    cur_page_num = cur_page.number
    # 底部导航范围
    page_range = list(range(max(1,cur_page_num-4),min(cur_page_num+4,paginator.num_pages)+1))
    # 省略号
    if page_range[0]>2:
        page_range.insert(0,"...")
    if page_range[-1]<paginator.num_pages-1:
        page_range.append("...")
    # 首位页始终显示
    if page_range[0]!=1:
        page_range.insert(0,1)
    if page_range[-1]!=paginator.num_pages:
        page_range.append(paginator.num_pages)
    context['page_range'] = page_range
    context['cur_page'] = cur_page
    context['item_number'] = all_item_list.count()
    context['items_with_record_info'] = all_item_list
    return context

def item_list(request):
    items_with_record_info = Item.objects.annotate(
        record_num=Count('record'),
        min_price=Min('record__price'),
        max_price=Max('record__price'),
        last_record_date=Max('record__scrape_time'),
        first_record_date=Min('record__scrape_time'),
    ).order_by('-id')
    for item in items_with_record_info:
        item.last_price = item.record_set.last().price
    context = item_list_common_data(request,items_with_record_info)
    context['favorite_items'] = Favorite.objects.all()
    return render(request,'item_list.html',context)

def favorite_list(request):
    items_with_record_info = Item.objects.filter(is_favorite=True).annotate(
        record_num=Count('record'),
        min_price=Min('record__price'),
        max_price=Max('record__price'),
        last_record_date=Max('record__scrape_time'),
        first_record_date=Min('record__scrape_time'),
    ).order_by('-favorite__add_time')
    for item in items_with_record_info:
        item.last_price = item.record_set.last().price
    context = item_list_common_data(request,items_with_record_info)
    return render(request,'favorite_list.html',context)

def item_detail(request,item_id):
    context = {}
    item = get_object_or_404(Item,id=item_id)
    context['item'] = item
    record_values = item.record_set.annotate(
        per_id=Window(expression=DenseRank(),partition_by='item',order_by='scrape_time')
    ).order_by('scrape_time')
    for i in range(1,len(record_values)):
        if record_values[i].price > record_values[i-1].price:
            record_values[i].price_change = "↑"
            record_values[i].change_rate = str(round(100*(record_values[i].price - record_values[i-1].price)/record_values[i-1].price,2))+"%"
        elif record_values[i].price < record_values[i-1].price:
            record_values[i].price_change = "↓"
            record_values[i].change_rate = str(round(100*(record_values[i].price - record_values[i-1].price)/record_values[i-1].price,2))+"%"
    context['record_values'] = record_values
    context['srcs'] = item.img_set.values_list('src',flat=True) # 只获得值的方法
    context['record_num'] = Record.objects.filter(item_id=item_id).count()
    context['min_price'] = item.record_set.order_by('price')[0].price
    context['max_price'] = item.record_set.order_by('price').reverse()[0].price
    return render(request,'item_detail.html',context)


# 添加和取消收藏
def fav_add(request):
    if request.method == "GET":
        item_id = int(request.GET.get('item_id'))
        in_fav = request.GET.get('in_fav')
        item = Item.objects.get(id=item_id)
        data = {}
        if in_fav == 'false':
            item.is_favorite = True
            item.save()
            try:
                Favorite.objects.create(item=item)
            except IntegrityError:
                data['i'] = "添加失败，已存在"
            else:
                data['i'] = "添加成功"
        elif in_fav == 'true':
            item.is_favorite = False
            item.save()
            try:
                Favorite.objects.get(item=item).delete()
            except exceptions.ObjectDoesNotExist:
                data['i'] = "删除失败，该收藏不存在"
            else:
                data['i'] = "删除成功"
        data['before'] ,data['after'] = in_fav, item.is_favorite
        data['name'] = item.name
        return JsonResponse(data)
    
# 一键爬取
def function_of_check_all(url):
    try:
        item_info = get_certain_item_info(url)
    except:
        return 0
    else:
        save_item_or_add_record_on_exist_item(url,item_info)
        return 1
# def check_all(request):
#     referer = request.META.get('HTTP_REFERER',reverse('item_list'))
#     if request.method == "POST":
#         if request.POST.get("check") == 'all_fav_list':
#             all_items = Item.objects.filter(is_favorite=True)
#         elif request.POST.get("check") == 'all_item_list': 
#             all_items = Item.objects.all()
#         elif request.POST.get('check') == 'this_page_item_list' and request.POST.get('page_num'):
#             all_all_items = Item.objects.all()
#             cur_page = int(request.POST.get('page_num'))
#             num = settings.EACH_PAGE_OBJ_NUM
#             all_items = all_all_items[num*(cur_page-1):num*cur_page]
#         start_time = time.time()
#         urls = all_items.values_list('url',flat=True)
#         result_list = []
#         for i in range(len(urls)):
#             result_list.append(function_of_check_all(urls[i]))
#         end_time = time.time()
#         info = f"共{all_items.count()}条,成功{result_list.count(1)}条,耗时{round(end_time - start_time,3)}秒"
#         messages.add_message(request,messages.SUCCESS,info)
#         if 0 in result_list:
#             error_info = f",失败{result_list.count(0)}条"
#             messages.error(request,error_info)
#     return redirect(referer)

# 合并相同记录
def merge_same_record(request):
    item_id = request.GET.get('item_id')
    item = Item.objects.get(id=item_id)
    records = item.record_set.order_by('-scrape_time')
    for r in range(1,len(records)-1):
        if records[r].price == records[r-1].price and records[r].price == records[r+1].price:
            records[r].delete()
    return JsonResponse({})



def check_all(request):
    referer = request.META.get('HTTP_REFERER',reverse('item_list'))
    if request.method == "POST":
        if request.POST.get("check") == 'all_fav_list':
            all_items = Item.objects.filter(is_favorite=True)
        elif request.POST.get("check") == 'all_item_list': 
            all_items = Item.objects.all()
        elif request.POST.get('check') == 'this_page_item_list' and request.POST.get('page_num'):
            all_all_items = Item.objects.all()
            cur_page = int(request.POST.get('page_num'))
            num = settings.EACH_PAGE_OBJ_NUM
            all_items = all_all_items[num*(cur_page-1):num*cur_page]
        start_time = time.time()
        urls = all_items.values_list('url',flat=True)
        for url in urls:
            t = PeriodicTask.objects.create(
                name = str(random.randint(10001,20000)),
                
            )


        result_list = []
        for i in range(len(urls)):
            result_list.append(function_of_check_all(urls[i]))
        end_time = time.time()
        info = f"共{all_items.count()}条,成功{result_list.count(1)}条,耗时{round(end_time - start_time,3)}秒"
        messages.add_message(request,messages.SUCCESS,info)
        if 0 in result_list:
            error_info = f",失败{result_list.count(0)}条"
            messages.error(request,error_info)
    return redirect(referer)