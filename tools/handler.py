#!/usr/bin/python
# coding=utf-8

import django,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djtest.settings")
django.setup()
from tools.db import Db_MySql
# from djcelery import models as djcelery_model
from rbmapi import rbm_manage
from tools.ms import ms_exec_test
from test1.models import Routing_keys
from djcelery import loaders
from celery import registry

b = Db_MySql('10.10.6.11', 'root', 'root', 'djtest')

def get_all_tasks_info():
    sql = '''select a.id, a.task_id, a.status, a.result, b.log_date, a.date_done, b.`first`, b.`second`
from celery_taskmeta a , test1_add b
where a.task_id = b.task_id order by a.id'''

    res = b.ExecQuery(sql)
    return res


def add_task_to_db(name, task, queue, exchange, routing_key, enabled, date_changed, interval_id, args='[]', kwargs='{}'):
    if interval_id == 0:
        sql = '''
        insert into djcelery_periodictask(name,task,args,kwargs,queue,exchange,routing_key,enabled,total_run_count,date_changed,description) 
        values(%s,%s,%s,%s,%s,%s,%s,%s,0,%s,'')
        '''
        para = (name, task, args, kwargs, queue, exchange, routing_key,enabled, date_changed)
    else:
        sql = '''
        insert into djcelery_periodictask(name,task,args,kwargs,queue,exchange,routing_key,enabled,total_run_count,date_changed,description,interval_id) 
        values(%s,%s,%s,%s,%s,%s,%s,%s,0,%s,'',%s)
        '''
        para = (name, task, args, kwargs, queue, exchange, routing_key,enabled, date_changed, interval_id)

    res = b.ExecNoQuery(sql, para)
    return res

#更新任务
def update_task_with_id(id, task, queue, exchange, routing_key, enabled, date_changed, interval_id, kwargs='{}'):
    sql = '''
    update djcelery_periodictask set task=%s,kwargs=%s,queue=%s,exchange=%s,routing_key=%s,enabled=%s,date_changed=%s,interval_id=%s 
    where id=%s
    '''
    para = (task, kwargs, queue, exchange, routing_key,enabled, date_changed, interval_id, id)
    res = b.ExecNoQuery(sql, para)
    return res

#添加 interval 2 db
def add_interval_to_db(every, period):
    sql = '''
    insert into djcelery_intervalschedule(every,period) values(%s,%s)
    '''
    para = (every, period)
    res = b.ExecNoQuery(sql, para)
    return res

#获取 interval 列表
def get_interval_list():
    sql = '''
    select id,concat_ws(" ",cast(every as char),period) period from djcelery_intervalschedule
    '''
    r = b.ExecQuery(sql)
    return r


def get_interval_list_sep_all():
    sql = '''
    select id, every, period from djcelery_intervalschedule
    '''
    r = b.ExecQuery(sql)
    return r

def update_interval_data(id, every, period):
    sql = '''
    update djcelery_intervalschedule set every=%s,period=%s where id=%s
    '''
    para = (every, period, id)
    res = b.ExecNoQuery(sql, para)
    return res

def delete_interval_data(id_list):
    res_list = []
    sql = """
            delete from djcelery_intervalschedule where id=%s
            """
    res_list = [b.ExecNoQuery(sql, id) for id in id_list]
    # for id in id_list:
    #     res = b.ExecNoQuery(sql, id)
    #     # res = djcelery_model.IntervalSchedule.objects.filter(id=id).delete()
    #     res_list.append(res)
    for r in res_list:
        if r == 'False':
            return False
    return True


def get_crontab_list_sep_all():
    sql = '''
    select id, hour, minute, day_of_week, day_of_month, month_of_year from djcelery_crontabschedule
    '''
    r = b.ExecQuery(sql)
    return r

def update_crontab_data(id, hour, minute, day_of_week, day_of_month, month_of_year):
    sql = '''
    update djcelery_crontabschedule set hour=%s, minute=%s, day_of_week=%s, 
    day_of_month=%s, month_of_year=%s where id=%s
    '''
    para = (hour, minute, day_of_week, day_of_month, month_of_year, id)
    res = b.ExecNoQuery(sql, para)
    return res

def add_crontab_to_db(hour, minute, day_of_week, day_of_month, month_of_year):
    sql = '''
    insert into djcelery_crontabschedule(hour, minute, day_of_week, day_of_month, month_of_year) 
    values(%s,%s,%s,%s,%s)
    '''
    para = (hour, minute, day_of_week, day_of_month, month_of_year)
    res = b.ExecNoQuery(sql, para)
    return res


def delete_crontab_data(id_list):
    res_list = []
    sql = """
            delete from djcelery_crontabschedule where id=%s
            """
    res_list = [b.ExecNoQuery(sql, id) for id in id_list]
    # for id in id_list:
    #     res = b.ExecNoQuery(sql, id)
    #     # res = djcelery_model.IntervalSchedule.objects.filter(id=id).delete()
    #     res_list.append(res)
    for r in res_list:
        if r == 'False':
            return False
    return True


def get_tasks_status():
    sql = '''
    select DISTINCT(a.name), a.task, a.enabled, a.last_run_at, b.state, a.id
    from djcelery_periodictask a
    LEFT JOIN djcelery_taskstate b
    on a.task = b.name
    '''
    res = b.ExecQuery(sql)
    return res


#获取任务明细
def get_task_detail(tid):
    sql = '''
    select a.id, a.name, a.task, a.kwargs, a.queue, a.exchange, a.routing_key, b.id interval_id, concat_ws(" ",cast(b.every as char),b.period) period
    from djcelery_periodictask a, djcelery_intervalschedule b
    where a.interval_id = b.id and a.id=%s
    '''

    res = b.ExecQuery(sql, tid)
    return res


def get_running_tasks():
    sql = '''
    SELECT a.name, a.state,a.kwargs,a.result,a.runtime ,b.date_done,c.hostname
    FROM djcelery_taskstate a
    LEFT JOIN celery_taskmeta b
    on a.task_id = b.task_id
    LEFT JOIN djcelery_workerstate c
    on a.worker_id = c.id
    order by b.date_done desc
    limit 50
    '''
    res = b.ExecQuery(sql)
    return res


def get_all_tasks():
    exclude_task = [
        'celery.backend_cleanup',
        'celery.chain',
        'celery.chord',
        'celery.chord_unlock',
        'celery.chunks',
        'celery.group',
        'celery.map',
        'celery.starmap',
        'djtest.celery.debug_task'
    ]
    loaders.autodiscover()
    task_list_all = list(sorted(registry.tasks.regular().keys()))
    for t in exclude_task:
        task_list_all.remove(t)
    return task_list_all


'''
rabbitmq
'''
#同步 exchanges 2 db
def rbt_sync_exchanges(name):
    sql = 'insert into test1_exchanges(name) values(%s)'
    try:
        res = b.ExecNoQuery(sql, name)
    except Exception as e:
        res = False
    return res

#同步 queues 2 db
def rbt_sync_queues(name):
    sql = 'insert into test1_queues(name) values(%s)'
    try:
        res = b.ExecNoQuery(sql, name)
    except Exception as e:
        res = False
    return res

#同步 routing_keys 2 db
def rbt_sync_routingkey(name, eid, qid):
    rk = Routing_keys.objects.get_or_create(name=name,exchange_id=eid,queue_id=qid)
    return rk[1]


def get_exchanges_db(cp=None, ps=None):
    if cp is None and ps is None:
        sql = 'select * from test1_exchanges'
        res = b.ExecQuery(sql)
    else:
        p1 = (cp-1)*ps
        sql = 'select * from test1_exchanges limit %s,%s'
        para = (p1, ps)
        res = b.ExecQuery(sql, para)
    return res


def get_queues_db(cp=None, ps=None):
    if cp is None and ps is None:
        sql = 'select * from test1_queues'
        res = b.ExecQuery(sql)
    else:
        #分页  cp 当前页，ps 每页显示数量
        p1 = (cp-1)*ps
        sql = 'select * from test1_queues limit %s,%s'
        para = (p1, ps)
        res = b.ExecQuery(sql, para)
    return res

#根据 exchange和 queue id获取 routing_key 列表
def get_routing_key_with_eq_id(eid, qid):
    rk = list(Routing_keys.objects.filter(exchange_id=eid, queue_id=qid).values('id','name'))
    return rk




if __name__ == '__main__':
    r = get_exchanges_db()
    # s = add_interval_to_db(55555, 'hours')
    # d = delete_interval_data([11,10])
    print(r)
    print(get_all_tasks())

    print(get_exchanges_db(cp=1,ps=5))

    # args = ('exec insertTestTable', 'None')
    # m = ms_exec_test(args)
    # print(m)

    # print(d)
    # el = ['11','12']
    # for e in el:
    #     print(rbt_sync(e))


    # a = add_task_to_db(name='ttt',task='ttt',enabled=0,interval_id=2,kwargs='{11}',queue='11',exchange='11',routing_key='11',date_changed='2018-08-04 01:01:01')
    # print(a)


