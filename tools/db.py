#!/usr/bin/python
# coding=utf-8


import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime

class Db_MySql:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def __dbconn(self):
        self.conn = pymysql.connect(self.host, self.user, self.password, self.database)
        cursor = self.conn.cursor(DictCursor)
        if not cursor:
            raise (NameError, 'connected failed')
        else:
            return cursor

    def ExecQuery(self, sql, para=None):
        with self.__dbconn() as cur:
            cur.execute(sql, para)
            res = cur.fetchall()
        return res

    def ExecNoQuery(self, sql, para=None):
        with self.__dbconn() as cur:
            cur.execute(sql, para)
            self.conn.commit()
            if cur.rowcount != 0:
                print('success')
                return True
            else:
                print('fail')
                return False



if __name__ == '__main__':
    b = Db_MySql('localhost', 'root', '12345678', 'djtest')
    sql = 'select id,concat_ws(" ",cast(every as char),period) period from djcelery_intervalschedule'
    r = b.ExecQuery(sql)
    print(r)

    # sql1 = 'insert into test1_add(task_id,log_date) values(%s,%s)'
    # para = ('1', datetime.now())
    # print(b.ExecNoQuery(sql1, para))

