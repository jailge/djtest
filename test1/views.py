from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from djcelery import models as celery_models
from djcelery import loaders
from celery.exceptions import SoftTimeLimitExceeded
from test1 import tasks
from test1.models import Add
from django.utils import timezone
from test1.models import Exchanges, Queues
from tools.handler import get_all_tasks_info, add_task_to_db, add_interval_to_db, get_interval_list, get_tasks_status, get_task_detail, get_interval_list_sep_all, update_interval_data, delete_interval_data
from tools.handler import get_crontab_list_sep_all, update_crontab_data, add_crontab_to_db, delete_crontab_data, update_task_with_id
from tools.handler import rbt_sync_routingkey, rbt_sync_exchanges, rbt_sync_queues, get_exchanges_db, get_queues_db, get_running_tasks, get_routing_key_with_eq_id
from tools.handler import get_all_tasks
from tools.supervisorctl import restart_beat
from celery import signature, chain, chord, group
from tools.msodbc import Odbc_Ms
from rbmapi import rbm_manage
from tools.ms import chain_task, group_task, ms_exec_test
from celery import registry
from .form import AddForm, SysConfigForm, IntervalForm
from test1.models import Exchanges, Queues, superuser
import re
import json




# Create your views here.

def dashboard(request):
    return render(request, 'test1/dashboard.html')

def chart_bar(request):
    if request.method == 'POST':
        tasks = list(celery_models.PeriodicTask.objects.all().values())
        return JsonResponse({'tasks_num':tasks})


def index(request):
    if request.method == 'POST':
        form = AddForm(request.POST, initial={'IntervalList':'seconds'})
        if form.is_valid():
            a = form.cleaned_data['a']
            b = form.cleaned_data['b']
            return HttpResponse(str(int(a) + int(b)))
    else:
        form = AddForm()

    return render(request, 'test1/index.html', {'form':form})
    # return render(request, 'test1/index.html')

def detail(request, task_id):
    task = get_object_or_404(celery_models.PeriodicTask, id=task_id)
    interval = celery_models.IntervalSchedule.objects.filter(id=task.interval_id).values()
    exchanges = Exchanges.objects.filter(name=task.exchange).values()
    queues = Queues.objects.filter(name=task.queue).values()
    td = task_id
    t = get_task_detail(task_id)

    task_dict = {
        'name': task.name,
        'task': task.task,
        'kwargs': task.kwargs,
        'queue': task.queue,
        'exchange': task.exchange,
        'routing_key': task.routing_key,
        'enabled': task.enabled,
        'interval_id': task.interval_id
    }
    return render(request, 'test1/detail.html', locals())


def detail_p(request):
    print(request.POST)
    if request == 'POST':
        task_id = request.POST.get('task_id')
        t = get_task_detail(task_id)
        return JsonResponse({'detail': t})

def crontab_schedule(request):
    return render(request, 'test1/crontabschedule.html')

def interval_schedule(request):
    return render(request, 'test1/intervalschedule.html')

# @login_required(redirect_field_name='',login_url='/')
def rabbitmq(request):
    queues = rbm_manage.rbt_get_all_queues()
    return render(request, 'test1/rabbitmq.html', {'queues':queues})

def rabbitmq_sync(request):
    if request.method == 'POST':
        e = []
        q = []
        exchanges_list = rbm_manage.rbt_get_all_exchanges()
        queues_list = rbm_manage.rbt_get_all_queues()
        for el in exchanges_list:
            r = rbt_sync_exchanges(el)
            if r is not False:
                e.append(r)
        for ql in queues_list:
            s = rbt_sync_queues(ql)
            if s is not False:
                q.append(s)
        return  JsonResponse({'ex_num':e.__len__(), 'qu_num':q.__len__()})


#获取 tasks的列表
def get_registry_task(request):
    task_list_all = get_all_tasks()
    return JsonResponse({'task_list': task_list_all})


def get_exchanges(request):
    exlist = get_exchanges_db()
    if request.method == 'POST':
        return JsonResponse({'exchanges_list':exlist})
    else:
        return JsonResponse({'data':exlist, 'totals':exlist.__len__()})

def get_exchanges_table(request):
    num = get_exchanges_db()
    if request.method == 'POST':
        cp = int(request.POST.get('cPage'))
        ps = int(request.POST.get('pSize'))
        exlist = get_exchanges_db(cp=cp, ps=ps)
        return JsonResponse({'data':exlist, 'totals':num.__len__()})


def get_queues(request):
    qlist = get_queues_db()
    if request.method == 'POST':
        return JsonResponse({'queues_list':qlist})
    else:
        return JsonResponse({'data':qlist, 'totals':qlist.__len__()})

#queues 分页查询
def get_queues_table(request):
    num = get_queues_db()
    if request.method == 'POST':
        cp = int(request.POST.get('cPage'))
        ps = int(request.POST.get('pSize'))
        qlist = get_queues_db(cp=cp, ps=ps)
        return JsonResponse({'data':qlist, 'totals':num.__len__()})

def get_routing_key_eqid(request):
    if request.method == 'POST':
        eid = request.POST.get('exchange')
        qid = request.POST.get('queue')
        rk = get_routing_key_with_eq_id(eid=eid,qid=qid)
        return JsonResponse({'routing_key':rk})

def rabbitmq_add(request):
    return render(request, 'test1/addrbt.html')

def add_ex_qu_rk(request):
    if request.method == 'POST':
        exchange = request.POST.get('exchange')
        queue = request.POST.get('queue')
        routing_key = request.POST.get('routing_key')
        res_ex = rbm_manage.rbt_put_exchange(ex=exchange,type='direct',durable='true')
        res_qu = rbm_manage.rbt_put_queue(qu=queue,durable='true')
        res_rk = rbm_manage.rbt_post_binding(ex=exchange,qu=queue,routing_key=routing_key)
        if res_ex and res_qu and res_rk:
            res_ex_db = rbt_sync_exchanges(exchange)
            res_qu_db = rbt_sync_queues(queue)
        # ex_id = get_object_or_404(Exchanges, name)
            if res_ex_db and res_qu_db:
                ex_id = list(Exchanges.objects.filter(name=exchange).values('id'))[0]['id']
                qu_id = list(Queues.objects.filter(name=queue).values('id'))[0]['id']
                rk = rbt_sync_routingkey(name=routing_key,eid=ex_id,qid=qu_id)
                if rk:
                    status = 'true'
                else:
                    status = 'false'
            else:
                status = 'false'
        else:
            status = 'false'
        # if res_ex and res_qu and res_rk and res_ex_db and res_qu_db:
        #     status = 'true'
        # else:
        #     status = 'false'
        return JsonResponse({'status':status})

#rbt_queue 实时图
def queue_monitor(request):
    if request.method == 'POST':
        all_messages = rbm_manage.rbt_get_all_queues_messages()
        queues = [q for q in all_messages]
        messages = [all_messages[m]['messages'] for m in all_messages]
        unacked = [all_messages[m]['unacked'] for m in all_messages]
        ready = [all_messages[m]['ready'] for m in all_messages]
        return JsonResponse({'queues':queues,'messages':messages,'unacked':unacked,'ready':ready})



def add_interval_every_period(request):
    if request.method == 'POST':
        every = int(request.POST.get('every'))
        period = request.POST.get('period')
        res = add_interval_to_db(every, period)
        # print(res)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status': status})


def addtask(request):
    return render(request, 'test1/addtask.html')

def add_test(request):
    a = int(request.GET.get('a'))
    b = int(request.GET.get('b'))
    return HttpResponse(str(a + b))

# def index_form(request):
#     if request.method == 'POST':
#         form = AddForm(request.POST)
#         if form.is_valid():
#             a = form.cleaned_data['a']
#             b = form.cleaned_data['b']
#             return HttpResponse(str(int(a) + int(b)))
#         else:
#             form = AddForm()
#         return render(request, 'test1/index.html', {'form':form})

def add1(request):
    first = int(request.GET.get('first'))
    second = int(request.GET.get('second'))
    # result = chain(tasks.add.s(first, second), tasks.add.s(1), tasks.add.s(1))()
    # result = tasks.add.delay(first, second)
    result = chain_task(tasks.add, first, second, 1, 1)
    print(result)
    Add.objects.create(task_id=result.id, first=first, second=second, log_date=timezone.now())
    return render(request, 'test1/index.html')


def add_delay(request):
    first = int(request.GET.get('first_d'))
    second = int(request.GET.get('second_d'))
    result = tasks.add_delay.delay(first, second)
    print(result)
    Add.objects.create(task_id=result.id, first=first, second=second, log_date=timezone.now())
    return render(request, 'test1/index.html')

def add_timeout(request):
    first = int(request.GET.get('first_t'))
    second = int(request.GET.get('second_t'))
    try:
        result1 = tasks.add_timeout.delay(first, second)
    except SoftTimeLimitExceeded:
        result1.revoke()
    print(result1,result1.status)
    Add.objects.create(task_id=result1.id, first=first, second=second, log_date=timezone.now())
    return render(request, 'test1/index.html')

def result(request):
    res = get_all_tasks_info()
    return render(request, 'test1/result.html', {'result': res})

def db_exec(request):
    sql = request.GET.get('sql')
    para = request.GET.get('para')
    sqlist = [sql,]
    print(sqlist)
    res = tasks.db_exec.delay(sqlist)
    print(res)
    Add.objects.create(task_id=res.id, log_date=timezone.now())
    return render(request, 'test1/index.html')



def add_task(request):
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task = request.POST.get('task')
        enabled = request.POST.get('enabled')
        interval_id = request.POST.get('interval_id')
        kwargs = request.POST.get('kwargs')
        queue = request.POST.get('queue')
        exchange = request.POST.get('exchange')
        routing_key = request.POST.get('routing_key')
        date_changed = timezone.now()
        a = add_task_to_db(name=task_name, task=task, kwargs=kwargs, queue=queue, exchange=exchange,
                       routing_key=routing_key,enabled=enabled, date_changed=date_changed, interval_id=interval_id)
        # if enabled == 1:
        rb = restart_beat()
        print(rb)
        print(a)
        if a:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status':status})
    # task_name = request.GET.get('task_name')
    # task = request.GET.get('task')
    # enabled = int(request.GET.get('enabled'))
    # interval_id = int(request.GET.get('interval_id'))
    # arguments = request.GET.get('arguments')
    # queue = request.GET.get('queue')
    # exchange = request.GET.get('exchange')
    # routing_key = request.GET.get('routing_key')

    # ka = {'name':task_name, 'task':task, 'args':'[]', 'kwargs':arguments, 'queue':queue, 'exchange':exchange, 'routing_key':routing_key,
    #       'enabled':enabled, 'date_changed':date_changed, 'interval_id':interval_id}
    # l = [task_name, task, arguments, queue, exchange, routing_key,enabled, date_changed, interval_id]
    # print(task_name,task, arguments, queue, exchange, routing_key,enabled, date_changed, interval_id)
    # a = add_task_to_db(name=task_name, task=task, kwargs=arguments, queue=queue, exchange=exchange, routing_key=routing_key,
    #       enabled=enabled, date_changed=date_changed, interval_id=interval_id)
    # # a = add_task_to_db(name='ttt', task='ttt', enabled=0, interval_id=2, kwargs='{11}', queue='11', exchange='11',routing_key='11', date_changed='2018-08-04 01:01:01')
    # print(a)
    # if a:
    #     status = 'succeed'
    # else:
    #     status = 'failed'
    # return render(request, 'test1/index.html', {'task_status': status})

def update_task(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        task = request.POST.get('task')
        enabled = request.POST.get('enabled')
        interval_id = request.POST.get('interval_id')
        kwargs = request.POST.get('kwargs')
        queue = request.POST.get('queue')
        exchange = request.POST.get('exchange')
        routing_key = request.POST.get('routing_key')
        date_changed = timezone.now()
        res = update_task_with_id(id,task,queue,exchange,routing_key,enabled,date_changed,interval_id,kwargs)
        print(res)
        rb = restart_beat()
        print(rb)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status': status})

def get_running_tasks_table(request):
    res = get_running_tasks()
    return JsonResponse({'data':res})
    # return JsonResponse({'rows': res,'total':res.__len__()})


def add_interval(request):
    every = int(request.GET.get('every'))
    period = request.GET.get('period')
    inter = add_interval_to_db(every=every, period=period)
    if inter:
        status = 'succeed'
    else:
        status = 'failed'
    return render(request, 'test1/index.html', {'interval_status': status})



def get_tasks_list(request):
    tasks = list(sorted(registry.tasks.regular().keys()))
    p = r"\w+\.tasks\.w+"
    tasks_list = [re.findall(p, i)[0] for i in tasks if re.findall(p, i)]
    return render(request, 'test1/addtask.html')



def get_interval(request):

    interlist = get_interval_list()
    # return HttpResponse(json.dumps({'interval_list':interlist}))
    return JsonResponse({'rows':interlist, 'total':interlist.__len__()})
    # return JsonResponse({'interval_list':interlist})

def get_interval_list_p(request):
    if request.method == 'POST':
        # i_id = request.POST.get('interval_id')
        interval_list = get_interval_list()
        return JsonResponse({'interval_list': interval_list})

def get_interval_list_sep(request):
    interlist = get_interval_list_sep_all()
    return JsonResponse({'page':1,'rows':interlist, 'total':interlist.__len__()})

def update_interval(request):
    print(request.POST)
    if request.method == 'POST':
        id = request.POST.get('id')
        every = request.POST.get('every')
        period = request.POST.get('period')
        res = update_interval_data(id, every, period)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status':status})

def delete_interval(request):
    print('!!!!!')
    print(request.POST.get('data'))
    if request.method == 'POST':
        data_list = request.POST.get('data')
        p = r'\"id\":\d+'
        print(re.findall(p, data_list))
        data_list = re.findall(p, data_list)
        id_list = [d[5] for d in data_list]
        print(id_list)
        res = delete_interval_data(id_list)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status': status})


def get_crontab_list_sep(request):
    crontablist = get_crontab_list_sep_all()
    return JsonResponse({'rows':crontablist, 'total':crontablist.__len__()})

def update_crontab(request):
    print(request.POST)
    if request.method == 'POST':
        id = request.POST.get('id')
        hour = request.POST.get('hour')
        minute = request.POST.get('minute')
        day_of_week = request.POST.get('day_of_week')
        day_of_month = request.POST.get('day_of_month')
        month_of_year = request.POST.get('month_of_year')
        res = update_crontab_data(id,hour,minute,day_of_week,day_of_month,month_of_year)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status':status})


def add_crontab_all(request):
    if request.method == 'POST':
        hour = request.POST.get('hour')
        minute = request.POST.get('minute')
        day_of_week = request.POST.get('day_of_week')
        day_of_month = request.POST.get('day_of_month')
        month_of_year = request.POST.get('month_of_year')
        res = add_crontab_to_db(hour,minute,day_of_week,day_of_month,month_of_year)
        # print(res)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status': status})


def delete_crontab(request):
    print('!!!!!')
    print(request.POST.get('data'))
    if request.method == 'POST':
        data_list = request.POST.get('data')
        p = r'\"id\":\d+'
        print(re.findall(p, data_list))
        data_list = re.findall(p, data_list)
        id_list = [d[5] for d in data_list]
        print(id_list)
        res = delete_crontab_data(id_list)
        if res:
            status = 'true'
        else:
            status = 'false'
        return JsonResponse({'status': status})


def get_tasks_status_p(request):
    print(request.POST)
    if request.method == 'POST':
        tasks_status = get_tasks_status()
        # return JsonResponse({'data':tasks_status, 'totals':tasks_status.__len__()})
        return JsonResponse({'tasks_status': tasks_status})

def display_new_tasks(request):
    concat = request.POST
    print(concat)
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task = request.POST.get('task')
        enabled = request.POST.get('enabled')
        interval_id = request.POST.get('interval_id')
        kwargs = request.POST.get('kwargs')
        queue = request.POST.get('queue')
        exchange = request.POST.get('exchange')
        routing_key = request.POST.get('routing_key')
        dic = {
            'task_name': task_name,
            'task': task,
            'enabled': enabled,
            'interval_id': interval_id,
            'kwargs': kwargs,
            'queue': queue,
            'exchange': exchange,
            'routing_key': routing_key
        }
        return JsonResponse(dic)
    # inter_id = request.GET.get('interval_list.value')
    # return render(request, 'test1/index.html', {'inter_id':inter_id})

    # 登录界面
def login(request):
    return render(request, 'test1/login.html')

def loginVerify(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        users = superuser.objects.all()
        for user in users:
            if user.username == username and user.password == password:
                return HttpResponse('1')
        return HttpResponse('-1')
    else:
        return HttpResponse('0')





