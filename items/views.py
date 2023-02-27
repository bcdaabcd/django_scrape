from django.shortcuts import get_object_or_404,render
from django.core.paginator import Paginator
from .models import Item,Record,Favorite
from django.db.models import Count,Max,Min,Window
from django.db.models.functions import DenseRank
from django.conf import settings

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
