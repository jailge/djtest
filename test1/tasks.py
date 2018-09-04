#!/usr/bin/python
# coding=utf-8


from __future__ import absolute_import
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import time
from tools.ms import ms_test, group_task, ms_exec_test, chain_task
from celery.result import GroupResult
from celery.utils.log import get_task_logger



logger = get_task_logger(__name__)


@shared_task(bind=True)
def add(self,x, y):
    print(
        'Executing task id {0.id}, kwargs {0.kwargs!r}, hostname {0.hostname}, delivery_info {0.delivery_info}, called_directly {0.called_directly}, reply_to {0.reply_to}'.format(
            self.request))
    return x + y

@shared_task(bind=True)
def add_ch(self,first, second):
    print(
        'Executing task id {0.id}, kwargs {0.kwargs!r}, hostname {0.hostname}, delivery_info {0.delivery_info}, called_directly {0.called_directly}, reply_to {0.reply_to}'.format(
            self.request))
    # result = chain_task(add, first, second, 1, 1)
    result = add.apply_async((2,2),queue='dj_for_add',routing_key='dj_for_add')
    return result


@shared_task
def add_delay(x, y):
    time.sleep(10)
    return x + y

@shared_task
def add_timeout(x, y):
    time.sleep(40)
    z = x + y
    return z

@shared_task
def db_test(**kwargs):
    # sql1 = "select * from Task where id=?"
    l = [(kwargs['sql1'], kwargs['para1'], kwargs['all1']), (kwargs['sql2'], kwargs['para2'], kwargs['all2'])]
    re = group_task(ms_test, l)
    return re
    # if re.ready() and re.successful():
        # return re.get()


@shared_task(bind=True)
def db_exec_test(self, **kwargs):
    print('Executing task id {0.id}, kwargs {0.kwargs!r}, hostname {0.hostname}, delivery_info {0.delivery_info}, called_directly {0.called_directly}, reply_to {0.reply_to}'.format(self.request))
    logger.info('Executing task id {0.id}, args:{0.args!r}, kwargs:{0.kwargs!r}'.format(self.request))
    l = [kwargs[k] for k in kwargs]
    l1 = l[::2]
    l2 = l[1::2]
    la = list(zip(l1, l2))
    print('=======la========')
    print(la)
    # ll = [(kwargs['sql1'], kwargs['para1']), (kwargs['sql2'], kwargs['para2'])]
    try:
        re = list(map(ms_exec_test, la))

    except Exception as e:
        raise self.retry(exc=e, countdown=5, max_retries=3)
    # re = group_task(ms_exec_test, la)
    return re


@shared_task
def db_exec(sqlist):
    print(sqlist)
    re = list(map(ms_exec_test, sqlist))
    print(re)
    return re






