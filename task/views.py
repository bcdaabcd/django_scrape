import json,re
from django_celery_beat.models import PeriodicTask,IntervalSchedule
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings
from items.models import Item
from task.models import TaskCategory

def task_list_common_data(request,all_tasks):
    context = {}
# 分页
    paginator = Paginator(all_tasks,settings.EACH_PAGE_OBJ_NUM)
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
    context['task_number'] = len(all_tasks)
    context['tasks_with_info'] = all_tasks
    return context

def task_list(request):
    all_tasks = PeriodicTask.objects.exclude(name="celery.backend_cleanup").order_by('-start_time')
    for t in all_tasks:
        info_dict = json.loads(t.kwargs)
        t.item = Item.objects.get(url=info_dict['url'])
        t.email = info_dict['email'] if info_dict['email'] else ""
        t.email_when = info_dict['email when'].replace('email ','')
        t.price_lt = info_dict['price lt']
        t.save()
    context = task_list_common_data(request,all_tasks)
    context['categories'] = TaskCategory.objects.all()
    return render(request,'task_list.html',context)

def task_with_category(request,category_id):
    category = TaskCategory.objects.get(id=category_id)
    all_tasks = PeriodicTask.objects.exclude(name="celery.backend_cleanup").filter(kwargs__contains=category.name.replace('email ',''))
    for t in all_tasks:
        info_dict = json.loads(t.kwargs)
        t.item = Item.objects.get(url=info_dict['url'])
        t.email = info_dict['email']
        t.email_when = info_dict['email when']
        t.save()
    context = task_list_common_data(request,all_tasks)
    context['category'] = category
    return render(request,'task_with_category.html',context)



def change_task_status(request):
    task_id = request.GET.get('task_id')
    was_on = request.GET.get('was_on')
    task = PeriodicTask.objects.get(id=task_id)
    data = {}
    if was_on == 'true':
        if task.enabled == True:
            task.enabled = False
            data['i'] = '任务暂停'
        elif task.enabled == False:
            data['i'] = '错误，此任务已处于暂停状态'
    elif was_on == 'false':
        if task.enabled == False:
            task.enabled = True
            data['i'] = '任务开始'
        else:
            task['i'] = '错误，次任务已处于进行状态'
    task.save()
    data['id'] = task_id
    data['before'] = was_on
    data['after'] = task.enabled
    return JsonResponse(data)

def start_or_stop_all(request):
    fro = request.GET.get('from')
    action = request.GET.get('action')
    data = {}
    if fro == 'task_list':
        if action == 'start':
            for t in PeriodicTask.objects.exclude(name="celery.backend_cleanup"):
                if t.enabled == False:
                    t.enabled = True
                    t.save()
        elif action == 'stop':
            for t in PeriodicTask.objects.exclude(name="celery.backend_cleanup"):
                if t.enabled == True:
                    t.enabled = False
                    t.save()
    elif fro == 'task_with_category':
        category_id = int(request.GET.get('category_id'))
        category = TaskCategory.objects.get(id=category_id)
        all_tasks = PeriodicTask.objects.exclude(name="celery.backend_cleanup").filter(kwargs__contains=category.name.replace('email ',''))
        if action == 'start':
            for t in all_tasks:
                if t.enabled == False:
                    t.enabled = True
                    t.save()
        elif action == 'stop':
            for t in all_tasks:
                if t.enabled == True:
                    t.enabled = False
                    t.save()
    data['from'] = fro
    data['action'] = action
    return JsonResponse(data)

def task_info_edit(request):
    if request.method == 'GET':
        task_id = request.GET.get('task_id')
        new_value = request.GET.get('new_email')
        target = request.GET.get('target')
        task = PeriodicTask.objects.get(id=task_id)
        info = json.loads(task.kwargs)
        d = {}
        if target == 'email':
            info['email'] = new_value
            task.kwargs = json.dumps(info)
            d['new_email'] = new_value
        elif target == 'interval':
            num = int(request.GET.get('interval_num'))
            period = request.GET.get('interval_period')
            task.interval.every = num
            task.interval.period = period
            task.interval.save()
            d['num'] = num
            d['period'] = period
        elif target == 'email when':
            new_email_when = request.GET.get('new_email_when')
            if new_email_when == 'when price lower than':
                new_price_lt = request.GET.get('new_price_lt')
                info['price lt'] = new_price_lt
                d['new_price_lt'] = new_price_lt
            info['email when'] = new_email_when
            task.kwargs = json.dumps(info)
            d['new_email_when'] = new_email_when
        task.save()
        d['target'] = target
        d['task_id'] = task_id
        d['new_task_info'] = info
        return JsonResponse(d)


