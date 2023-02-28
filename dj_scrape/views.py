import json,datetime,re,random,multiprocessing
from django.shortcuts import render,redirect,HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count,Max,Min
from django.contrib import auth
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask,IntervalSchedule
from django.urls import reverse
from django.conf import settings
from items.models import Item,Record,Favorite,Img
from task.models import TaskCategory
from .forms import SignInForm,SignUpForm
from items.views import item_list_common_data
from task.views import task_list_common_data
from .utils import get_certain_item_info,save_item_or_add_record_on_exist_item

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
                                    sch.delete()
                                    break
                                sch.delete()
                                break
                        else:
                            context['error_info'] = "任务创建成功"
                            PeriodicTask.objects.create(
                                name = str(random.randint(10001,20000)),
                                interval = sch,
                                task = 'task.tasks.periodic_task',
                                start_time = datetime.datetime.now(),
                                kwargs=json.dumps({
                                    'name':item_info['name'],
                                    'url':url,
                                    'email':"",
                                    'email when':"check only",
                                    'price lt':""
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
                                        sch.delete()
                                        break
                                    elif email != info['email']:
                                        context['error_info'] = "该商品已存在对其他邮箱的定时发送任务,您可前往修改邮箱(本次数据已保存)" 
                                        sch.delete()
                                        break
                                sch.delete()
                                break
                        else:
                            context['error_info'] = "任务创建成功"
                            PeriodicTask.objects.create(
                                name = str(random.randint(0,10000)),
                                interval = sch,
                                task = 'task.tasks.periodic_task',
                                start_time = datetime.datetime.now(),
                                kwargs=json.dumps({
                                    'name':item_info['name'],
                                    'url':url,
                                    'email':email,
                                    'email when':"email every check",
                                    'price lt':""
                                    }),
                                )
                    if request.POST.get("email_when_price"):
                        email = request.POST.get('email')
                        change_detail = request.POST.get("email_when_price")
                        for task in PeriodicTask.objects.exclude(name="celery.backend_cleanup"):
                            if url == json.loads(task.kwargs)['url']:
                                context['error_info'] = "此商品已存在任务，您可前往修改发送状态(本次数据已保存)"
                                sch.delete()
                                break
                        else:
                            if change_detail == "price drop":
                                price_lt = ""
                            elif change_detail == "price lower than":
                                price_lt = int(request.POST.get("price_lt"))
                            PeriodicTask.objects.create(
                                name = str(random.randint(20000,30000)),
                                interval = sch,
                                task = 'task.tasks.periodic_task',
                                start_time = datetime.datetime.now(),
                                kwargs=json.dumps({
                                    'name':item_info['name'],
                                    'url':url,
                                    'email':email,
                                    'email when':"email when "+change_detail,
                                    'price lt':price_lt, # 区分每逢降价和降到一定价格
                                })
                            )
            context['item_info'] = item_info
            # 以下仅为测试
            context['periodic_check'] = request.POST.get('periodic_check')
            context['time_num'] = request.POST.get('interval_num')
            context['interval_period'] = request.POST.get('interval_period')
            context['email_every_check'] = request.POST.get('email_every_check')
            context['email_when_price'] = request.POST.get("email_when_price")
            context['price_lt'] = request.POST.get("price_lt")
    return render(request,'input.html',context)

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
                    task_list.append(task)
            for t in task_list:
                info_dict = json.loads(t.kwargs)
                t.item = Item.objects.get(url=info_dict['url'])
                t.email = info_dict['email']
                t.email_when = info_dict['email when']
                t.save()
            context = task_list_common_data(request,task_list)
            context['categories'] = TaskCategory.objects.all()
            return render(request,'task_list.html',context)
        elif request.GET.get('from') == 'task-with-category':
            category_id = int(request.GET.get('category_id'))
            category = TaskCategory.objects.get(id=category_id)
            task_list = []
            for task in PeriodicTask.objects.exclude(name="celery.backend_cleanup").filter(kwargs__contains=category.name.replace('email ','')):
                info_dict = json.loads(task.kwargs)
                if re.search(kw,info_dict['name'],re.I):
                    task_list.append(task)
            for t in task_list:
                info_dict = json.loads(t.kwargs)
                t.item = Item.objects.get(url=info_dict['url'])
                t.email = info_dict['email']
                t.email_when = info_dict['email when']
                t.save()
            context = task_list_common_data(request,task_list)
            context['category'] = category
            return render(request,'task_with_category.html',context)

# 删除task或者item
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

# # 登录
# def sign_in(request):
#     if request.method == 'POST':
#         sign_in_form = SignInForm(request.POST)
#         if sign_in_form.is_valid():
#             user = sign_in_form.cleaned_data['user']
#             auth.login(request,user)
#             return redirect(reverse('url_input'))
#     else:
#         sign_in_form = SignInForm()
#     context = {}
#     context['sign_in_form'] = sign_in_form
#     return render(request,'sign_in.html',context)

# # 注册
# def sign_up(request):
#     if request.method == 'POST':
#         sign_up_form = SignUpForm(request.POST)
#         if sign_up_form.is_valid():
#             name = sign_up_form.cleaned_data['name']
#             password = sign_up_form.cleaned_data['password']
#             email = sign_up_form.cleaned_data['email']
#             User.objects.create_user(name,email,password)
#             user = auth.authenticate(request,username=name,password=password)
#             auth.login(request,user)
#             return redirect(reverse('url_input'))
#     else:
#         sign_up_form = SignUpForm()
#     context = {}
#     context['sign_up_form'] = sign_up_form
#     return render(request,'sign_up.html',context)

# # 登出
# def log_out(request):
#     auth.logout(request)
#     return redirect(request.GET.get('from',reverse('url_input')))

# # 用户信息
# def user_info(request):
#     context = {}
#     return render(request,'user_info.html',context)

