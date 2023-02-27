import json,datetime,fake_useragent,re,random,multiprocessing,time,django
from urllib import request
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
from django.shortcuts import render,redirect,HttpResponse,get_object_or_404
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse,Http404
from django.core import exceptions
from django.contrib import messages
from django.db.models import Count,Max,Min
from django.db.utils import IntegrityError
from django.conf import settings
from django_celery_beat.models import PeriodicTask,IntervalSchedule,CrontabSchedule
from items.models import Item,Record,Favorite,Img
from task.models import TaskCategory
from items.views import item_list_common_data
from task.views import task_list_common_data

def simplify_or_supplement_url(url):
    if not (re.match(r"https://www.",url) or re.match(r"http://www.",url)):
        url = "https://www." + url
    pa = r"/dp/[0-9A-Z]+/?"
    if not re.search(pa,url):
        raise AttributeError
    required_min_length = re.search(pa,url).span()[1]
    new_url = url[:required_min_length]
    if not re.search(r"/$",new_url):
        new_url += '/'
    return new_url

def check_if_color_option_exist(soup):
    try:
        info_box = soup.find('div',id='variation_color_name')
        info = info_box.select_one('span.selection').text.strip()
    except AttributeError:
        info = None
    return info
def check_if_size_option_exist(soup):
    try:
        info_box = soup.find('div',id='variation_size_name')
        info = info_box.select_one('span.selection').text.strip()
    except AttributeError:
        info = None
    return info
def get_certain_item_info(url:str)->dict:
    ua = fake_useragent.UserAgent()
    headers = {'User-Agent': ua.random}
    reques = request.Request(url=url,headers=headers)
    response = request.urlopen(reques)
    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    try:
        src = soup.select_one("div.imgTagWrapper>img")['src']
    except TypeError: # 也许是游戏商品
        src = soup.select_one("img#js-masrw-main-image")['src']
    try:
        name = soup.find('span',id='productTitle').text.strip().replace(" ","")
    except AttributeError:
        name = soup.select_one('span#btAsinTitle').text.strip().replace(" ","")
    try:
        ori_price = soup.find('span', class_="a-offscreen").text
    except AttributeError:
        ori_price = soup.select_one('span#actualPriceValue>strong.priceLarge').text
    price = int("".join(re.findall(r"\d",ori_price)))
    size_info = check_if_size_option_exist(soup)
    color_info = check_if_color_option_exist(soup)
    return {'name':name,'price':price,'size':size_info,'color':color_info,'src':src}

def save_item_or_add_record_on_exist_item(url:str,item_info:dict):
    def save_img_if_not_exist_in_certain_item(item_info,item):
        try:
            img = Img.objects.get(src=item_info['src'])
        except exceptions.ObjectDoesNotExist:
            img = Img()
            img.src = item_info['src']
            img.item = item
            img.save()
        else:
            if img.item != item:
                img = Img()
                img.src = item_info['src']
                img.item = item
                img.save()
    item,created = Item.objects.get_or_create(url=url)
    if created:
        item.name = item_info['name']
        item.size = item_info['size']
        item.color = item_info['color']
        item.save()
    record = Record()
    record.item = item
    record.price = item_info['price']
    record.save()
    save_img_if_not_exist_in_certain_item(item_info,item)
    return item

def create_schedule(num:int,interval_period:str)->IntervalSchedule:
    if interval_period == "second":
        period = IntervalSchedule.SECONDS
    if interval_period == "minute":
        period = IntervalSchedule.MINUTES
    elif interval_period == "hour":
        period = IntervalSchedule.HOURS
    elif interval_period == "day":
        period = IntervalSchedule.DAYS
    elif interval_period == "week":
        num *= 7
        period = IntervalSchedule.DAYS
    elif interval_period == "month":
        num *= 30
        period = IntervalSchedule.DAYS
    sch,created = IntervalSchedule.objects.get_or_create(every=num,period=period)
    return sch

def input(request):
    context = {}
    if request.method == 'POST':
        try:
            old_url = request.POST.get('url')
            url = simplify_or_supplement_url(old_url)
            item_info = get_certain_item_info(url)
        except TypeError:
            if old_url != "":
                context['error_info'] = "爬取失败，请重试"
        else:
            if request.POST.get('save'):
                save_item_or_add_record_on_exist_item(url,item_info)
                if request.POST.get('periodic_check'):
                    interval_num = int(request.POST.get('interval_num'))
                    interval_period = request.POST.get('interval_period')
                    sch = create_schedule(interval_num,interval_period)
                    if not request.POST.get('email_every_check'): # 未勾选发送邮件
                        for task in PeriodicTask.objects.exclude(name="celery.backend_cleanup"): #查找所有task中的url
                            info = json.loads(task.kwargs)
                            if url == info['url']: # 若此url存在
                                context['error_info'] = "该商品已存在定时检查任务(本次数据已保存)"
                                if info['email']:
                                    context['error_info'] = "该商品已存在定时发送邮件任务，您可前往清除邮箱(本次数据已保存)"
                                    break
                                break
                        else:
                            context['error_info'] = "任务创建成功"
                            PeriodicTask.objects.create(
                                name = str(random.randint(10001,20000)),
                                interval = sch,
                                task = 'task.tasks.check_only',
                                start_time = datetime.datetime.now(),
                                kwargs=json.dumps({
                                    'name':item_info['name'],
                                    'url':url,
                                    'email':"",
                                    })
                            )
                    elif request.POST.get('email_every_check'):
                        email = request.POST.get("email")
                        for task in PeriodicTask.objects.exclude(name="celery.backend_cleanup"): #查找所有task中的url
                            info = json.loads(task.kwargs)
                            if url == info['url']: # 若此url存在
                                context['error_info'] = "该商品已存在定时任务，您可前往添加邮箱(本次数据已保存)"
                                if info['email']:
                                    if email == info['email']:
                                        context['error_info'] = "该商品已存在对此邮箱的定时发送任务(本次数据已保存)"
                                        break
                                    elif email != info['email']:
                                        context['error_info'] = "该商品已存在对其他邮箱的定时发送任务(本次任务已创建)" 
                                        PeriodicTask.objects.create(
                                            name = '<email>'+str(random.randint(0,10000)),
                                            interval = sch,
                                            task = 'task.tasks.check_and_email',
                                            start_time = datetime.datetime.now(),
                                            kwargs=json.dumps({
                                                'name':item_info['name'],
                                                'url':url,
                                                'email':email,
                                            }),
                                        )
                                        break
                                break
                        else:
                            context['error_info'] = "任务创建成功"
                            PeriodicTask.objects.create(
                                name = '<email>'+str(random.randint(0,10000)),
                                interval = sch,
                                task = 'task.tasks.check_and_email',
                                start_time = datetime.datetime.now(),
                                kwargs=json.dumps({
                                    'name':item_info['name'],
                                    'url':url,
                                    'email':email,
                                    }),
                                )
                    # if request.POST.get("email_when_price"):
                    #     category_name = request.POST.get("email_when_price")
                    #     category = TaskCategory.objects.get(name=category_name)
                    #     if category_name == "price_drop":
                    #         Task.objects.create(item=item,cycle_number=interval_num,cycle_unit=interval_period,email=email,category=category)
                    #     if category_name == "price_lower_than":
                    #         price_number = int(request.POST.get("price_lt"))
                    #         Task.objects.create(item=item,cycle_number=interval_num,cycle_unit=interval_period,email=email,category=category,price_number=price_number)
            context['item_info'] = item_info
            # 以下仅为测试
            context['periodic_check'] = request.POST.get('periodic_check')
            context['time_num'] = request.POST.get('interval_num')
            context['interval_period'] = request.POST.get('interval_period')
            context['email_every_check'] = request.POST.get('email_every_check')
            context['email_when_price'] = request.POST.get("email_when_price")
            context['price_lt'] = request.POST.get("price_lt")
    return render(request,'input.html',context)

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

# 检索
def search(request):
    if request.method == "GET":
        kw = request.GET.get('keyword')
        if request.GET.get('from') == 'item-list':
            items_with_record_info = Item.objects.filter(name__icontains=kw).annotate(
                record_num=Count('record'),
                min_price=Min('record__price'),
                max_price=Max('record__price'),
                last_record_date=Max('record__scrape_time'),
                first_record_date=Min('record__scrape_time'),
            ).order_by('-id')
            context = item_list_common_data(request,items_with_record_info)
            context['favorite_items'] = Favorite.objects.all()
            return render(request,'item_list.html',context)
        elif request.GET.get('from') == 'fav-list':
            items_with_record_info = Item.objects.filter(name__icontains=kw,is_favorite=True).annotate(
                record_num=Count('record'),
                min_price=Min('record__price'),
                max_price=Max('record__price'),
                last_record_date=Max('record__scrape_time'),
                first_record_date=Min('record__scrape_time'),
            ).order_by('-id')
            context = item_list_common_data(request,items_with_record_info)
            return render(request,'favorite_list.html',context)
        elif request.GET.get('from') == 'task-list':
            task_list = []
            for task in PeriodicTask.objects.exclude(name="celery.backend_cleanup"):
                info_dict = json.loads(task.kwargs)
                if re.search(kw,info_dict['name'],re.I):
                    task.email = info_dict['email'] if info_dict['email'] else ""
                    task.item = Item.objects.get(url=info_dict['url'])
                    if task.interval:
                        task.type = task.interval.__class__.__name__.lower().replace('schedule','')
                    elif task.crontab:
                        task.type = task.crontab.__class__.__name__.lower().replace('schedule','')
                    task.save()
                    task_list.append(task)
            context = task_list_common_data(request,task_list)
            categories = []
            for taskcategory in TaskCategory.objects.all():
                taskcategory.name = taskcategory.content_type.model_class().__name__
                taskcategory.save()
                categories.append(taskcategory)
            context['categories'] = categories
            return render(request,'task_list.html',context)
        elif request.GET.get('from') == 'task-with-category':
            category_id = int(request.GET.get('category_id'))
            schedule_ct = ContentType.objects.get(taskcategory=category_id)
            schedule_class = schedule_ct.model_class()
            all_tasks = PeriodicTask.objects.none()
            if category_id == 2:
                all_schedukes = schedule_class.objects.exclude(minute=0,hour=4,day_of_week="*",day_of_month="*",month_of_year="*")
            elif category_id == 1:
                all_schedukes = schedule_class.objects.all()
            for schedule in all_schedukes:
                if schedule.periodictask_set.count() > 0:
                    all_tasks = all_tasks | schedule.periodictask_set.all()
            task_list = []
            for t in all_tasks:
                info_dict = json.loads(t.kwargs)
                if re.search(kw,info_dict['name'],re.I):
                    task_list.append(t)
                    t.item = Item.objects.get(url=info_dict['url'])
                    t.email = info_dict['email'] if info_dict['email'] else ""
                    if t.interval:
                        t.type = t.interval.__class__.__name__.lower().replace('schedule','')
                    elif t.crontab:
                        t.type = t.crontab.__class__.__name__.lower().replace('schedule','')
                    t.save()
            context = task_list_common_data(request,task_list)
            context['typename'] = schedule_class.__name__
            context['category_id'] = category_id
            return render(request,'task_with_category.html',context)

def delete_obj(request):    
    referer = request.META.get('HTTP_REFERER')
    if request.method == "GET":
        fro = request.GET.get('from')
        obj_id = int(request.GET.get('obj_id'))
        if fro == 'task_list' or fro == 'task_with_category':
            obj = PeriodicTask.objects.get(id=obj_id)
        elif fro == 'item_list' or fro == 'favorite_list':
            obj = Item.objects.get(id=obj_id)
        obj.delete()
    return redirect(referer)
