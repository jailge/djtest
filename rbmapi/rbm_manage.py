import django,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djtest.settings")
django.setup()
import requests
import json, re
from test1.models import Queues
# from tools.handler import get_queues_db

rbm_url = 'http://10.10.6.10:15672/api/'

def rbt_get_all_queues():
    exp = r'^celery.*'
    url = rbm_url + 'queues'
    res = requests.get(url, auth=('admin','admin'))
    res_j_dic = json.loads(res.content.decode())
    # r = [d['name'] for d in res_j_dic]
    # for i in res_j_dic:
    #     print (i['name'])
    r = [n['name'] for n in res_j_dic]
#过滤筛选出 celery 的 Queues
    qe = [re.findall(exp, q) for q in r ]
    qel = [qee[0] for qee in qe if qee.__len__() != 0]
#去除 celery 开头 的 Queues
    for qq in qel:
        r.remove(qq)
    # print(qel)
    return r

def rbt_get_all_exchanges():
    url = rbm_url + 'exchanges'
    res = requests.get(url, auth=('admin', 'admin'))
    res_j_dic = json.loads(res.content.decode())
    r = [n['name'] for n in res_j_dic]
    return r

def rbt_get_all_bindings():
    url = rbm_url + 'bindings'
    res = requests.get(url, auth=('admin', 'admin'))
    res_j_dic = json.loads(res.content.decode())
    # r = [n['name'] for n in res_j_dic]
    return res_j_dic

def rbt_put_exchange(ex, type, auto_delete=None, durable=None, internal=None, arguments=None):
    url = rbm_url + 'exchanges/%2f/{}'.format(ex)
    print(url)
    post_data = {
        'type': type,
        # 'auto_delete': auto_delete,
        'durable': durable,
        # 'internal': internal,
        # 'arguments': arguments
    }
    post_data = json.dumps(post_data)
    print(post_data)
    headers = {'content-type':'application/json'}
    res = requests.put(url, auth=('admin', 'admin'), data=post_data, headers=headers)
    if res.status_code == 201:
        return True
    else:
        print(res.status_code)
        return False

def rbt_put_queue(qu, auto_delete=None, durable=None, node=None, arguments=None):
    url = rbm_url + 'queues/%2f/{}'.format(qu)
    post_data = {
        # 'auto_delete': auto_delete,
        'durable': durable,
        # 'node': node,
        # 'arguments': arguments
    }
    if parcel_data(url,post_data,'put'):
        return True
    else:
        return False

def rbt_post_binding(ex, qu, routing_key):
    url = rbm_url + 'bindings/%2f/e/{0}/q/{1}'.format(ex,qu)
    post_data = {
        'routing_key': routing_key,
    }
    if parcel_data(url,post_data,'post'):
        return True
    else:
        return False


def rbt_get_all_queues_messages():
    url = rbm_url + 'queues/%2f/'
    ql = list(Queues.objects.all().values())
    # ql = get_queues_db()
    q_names = [q['name'] for q in ql]
    e_list = []
    message_dict = {}
    queues_messages = {}
    print(q_names)
    reg = r'^celery.+'
    for n in q_names:
        e = re.findall(reg, n)
        if e:
            e_list.append(e[0])
            # qq.remove(e)
    print(e_list)
    for i in e_list:
        q_names.remove(i)
    print(q_names)
    for q_n in q_names:
        url_q = url + q_n
        res = requests.get(url_q, auth=('admin', 'admin'))
        if res.status_code == 200:
            res_j_dic = json.loads(res.content.decode())
            # print(res_j_dic)
            queues_messages[q_n] = {
                'messages': res_j_dic["messages"],
                'unacked': res_j_dic["messages_unacknowledged"],
                'ready': res_j_dic["messages_ready"]
            }
        else:
            raise ('get messages error')
    return queues_messages


def parcel_data(url, data, para):
    post_data = json.dumps(data)
    headers = {'content-type': 'application/json'}
    res = ''
    if para == 'put':
        res = requests.put(url, auth=('admin', 'admin'), data=post_data, headers=headers)
    elif para == 'post':
        res = requests.post(url, auth=('admin', 'admin'), data=post_data, headers=headers)
    if res.status_code == 201:
        return True
    else:
        return False


if __name__ == '__main__':
    print(rbt_get_all_queues())
    m = rbt_get_all_queues_messages()
    print(m)
    q = [a for a in m]
    print(q)

    messages = [m[q]['messages'] for q in m]
    unacked = [m[q]['unacked'] for q in m]
    ready = [m[q]['ready'] for q in m]
    print(messages,unacked,ready)

    # post_d = {'type':"direct",'durable':'true'}
    # print(rbt_put_queue(qu='bbb',durable='true'))
    # print(rbt_put_exchange(ex='bbb', durable="true",type='direct'))
    # print(rbt_post_binding(ex='bbb',qu='bbb',routing_key='bbb'))