

import time, datetime


def compare_time(time1, time2):
    # if time1 > time2:
    #     return time1
    # t1 = datetime.datetime.now()
    # ti1 = time.strftime('%Y-%m-%d %H:%M:%S', time1)
    # ti2 = time.strftime('%Y-%m-%d %H:%M:%S', time2)
    t1 = datetime.datetime.strptime(time1, '%Y-%m-%d %H:%M:%S')
    t2 = datetime.datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
    delta = t1 - t2
    # print(ti1, ti2)
    return delta

def cp(a, b):
    return a['last_run_at'] - b['last_run_at']


if __name__ == '__main__':
    t1 = datetime.datetime.now()
    t2 = '2018-8-21 01:00:00'
    print(compare_time(t1, t2))


