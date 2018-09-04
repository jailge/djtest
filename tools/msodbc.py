#!/usr/bin/python
# coding=utf-8

import pyodbc


class Odbc_Ms:
    def __init__(self, server, database, uid, pwd):
        self.server = server
        self.database = database
        self.uid = uid
        self.pwd = pwd

    def __GetConnect(self):
        if not self.database:
            raise (NameError, 'no setting db info')

        self.conn = pyodbc.connect(
            'DRIVER={SQL Server}; SERVER=%s; port=1433; DATABASE=%s;UID=%s;PWD=%s;TDS_Version=8.0;' % (
            self.server, self.database, self.uid, self.pwd)
        )
        cur = self.conn.cursor()
        if not cur:
            return False
            # raise (NameError, "connected failed")
        else:
            return cur


    def ExecQuery(self, sql, para=None, all=False):
        with self.__GetConnect() as cur:
            if para is None:
                cur.execute(sql)
            else:
                cur.execute(sql, para)
            columns = [col[0] for col in cur.description]
            if not all:
                res = [dict(zip(columns, row)) for row in [cur.fetchall()][0]]
            else:
                res = [dict(zip(columns, row)) for row in cur.fetchall()]
        return res


    def ExecNoQuery(self, sql, para=None):
        with self.__GetConnect() as cur:
            if para is None:
                cur.execute(sql)
            else:
                cur.execute(sql, para)
            self.conn.commit()
            if cur.rowcount != 0:
                print("success")
                return True
            else:
                print("fail")
                return False



if __name__ == '__main__':
    ms = Odbc_Ms('10.10.6.66', 'test', 'sa', 'sa123')
    sql = 'select * from Task'
    re = ms.ExecQuery(sql, None, True)
    print(re)

    sql1 = 'exec insertTestTable'
    re1 = ms.ExecNoQuery(sql1, None)
    print(re1)




