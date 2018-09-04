
from tools.msodbc import Odbc_Ms
from celery import signature, chain, chord, group
from celery.task import task

@task
def ms_test(*args):
    ms = Odbc_Ms('10.10.6.66', 'test', 'sa', 'sa123')
    # sql = 'select * from Task'
    re = ms.ExecQuery(args[0], args[1], args[2])
    return re

@task
def ms_exec_test(args):
    print(args, '++++++')
    ms = Odbc_Ms('10.10.6.66', 'test', 'sa', 'sa123')
    if args[1] == 'None':
        re = ms.ExecNoQuery(args[0])
    else:
        re = ms.ExecNoQuery(args[0], args[1])
    if re:
        return True
    else:
        return False


def chain_task(fun, arg1, arg2, arg3, arg4):
    re = chain(fun.s(arg1, arg2), fun.s(arg3), fun.s(arg4)).apply_async(exchange='celery',queue='celery')
    return re


def chord_task(fun1, fun2, argslist):
    return chord((fun1.s(i) for i in argslist), fun2.s())()


def group_task(fun, argslist):
    return group(fun.s(i) for i in argslist)()


