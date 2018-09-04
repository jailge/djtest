from __future__ import absolute_import
from celery import shared_task
from celery.utils.log import get_task_logger
from rbmapi import rbm_manage
from test1 import models
from djcelery.models import PeriodicTask
from tools.comparetime import cp
from django.utils import timezone
from tools.supervisorctl import restart_beat
import time



logger = get_task_logger(__name__)
previous_id = 0

@shared_task(bind=True)
def q_manage(self):
    global previous_id
    print(
        'Executing task id {0.id}, kwargs {0.kwargs!r}, hostname {0.hostname}, delivery_info {0.delivery_info}, called_directly {0.called_directly}, reply_to {0.reply_to}'.format(
            self.request))
    logger.info(
        'Executing task id {0.id}, kwargs {0.kwargs!r}, hostname {0.hostname}, delivery_info {0.delivery_info}, called_directly {0.called_directly}, reply_to {0.reply_to}'.format(
            self.request))
    queue_messages_dict = rbm_manage.rbt_get_all_queues_messages()
    min_q_name = ''
    min_ua = 0
    max_ready = 0
    latest_id = 0
    last_time = timezone.now()
    for qm in queue_messages_dict:
        q_u = queue_messages_dict[qm]['ready']
        if q_u == 0:
            min_ua = q_u
            min_q_name = qm
            break
        if min_ua == 0:
            min_ua = q_u
        if q_u <= min_ua:
            min_ua = q_u
            min_q_name = qm
    print(min_q_name, min_ua)
    task = list(PeriodicTask.objects.filter(enabled=1).exclude(name='celery.backend_cleanup').exclude(name='q_manage').values('id','name','last_run_at','queue'))
    # task = list(PeriodicTask.objects.filter(enabled=1).values('id', 'name','last_run_at'))
    print(task)
    # print(task[0]['last_run_at'])
    # delta = timezone.now() - task[0]['last_run_at']
    # print(delta)
    # print(task.sort(key=lambda t:t['id']))
    for t in task:
        if t['last_run_at'] is None:
            continue
        elif t['last_run_at'] <= last_time:
            last_time = t['last_run_at']
            if t['id'] == previous_id and t['queue'] == min_q_name:
                print('previous_id:{}'.format(previous_id))
                return 'no transfer'
            else:
                previous_id = t['id']
                print('previous_id:{}'.format(previous_id))
                latest_id = t['id']
                latest_task_name = t['name']
                print(latest_id, last_time)
                q = PeriodicTask.objects.filter(id=latest_id).update(queue=min_q_name,exchange=min_q_name,routing_key=min_q_name)
                print(q)
                if q == 0:
                    return 'no alter'
                else:
                    if restart_beat():
                        return 'transfer {}-{}'.format(latest_id,latest_task_name)





if __name__ == '__main__':
    print(q_manage())

