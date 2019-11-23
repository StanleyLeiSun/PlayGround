# -*- coding: utf-8 -*-
"""
Wrapper of the Data Layer operations
https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-2017

"""
import datetime
import json
import pyodbc
import pymysql
import sqlite3
from entityClasses import Message, Action
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
import config

class RobertLogMSSQL:
    """Wrapper of the MSSQL"""
    def __init__(self,host,user,pwd,db, driver = '{SQL Server}'):
        self.server = host
        self.database = db
        self.username = user
        self.password = pwd
        self.driver= driver
        self.save_to_azuretable = True
        self.isMSSQL = driver == '{SQL Server}'
        self.isSQLite3 = driver == 'SQLite3'
        #self.driver= '{ODBC Driver 17 for SQL Server}'
        #self.driver= '{SQL Server Native Client 11.0}'
        self.isSQLite3 = False
        self.isMSSQL = True

        if self.save_to_azuretable:
            self.azuretable_service = TableService( \
            account_name=config.azuretable_account, account_key=config.azuretable_key)

    def __GetConnect(self):
        if self.isMSSQL:
            self.conn = pyodbc.connect('DRIVER=' + self.driver +\
            ';PORT=1433;SERVER='+self.server+\
            ';DATABASE='+self.database+\
            ';UID='+self.username+\
            ';PWD='+ self.password)
        elif self.isSQLite3:
            self.conn = sqlite3.connect(config.sqlite_db)
            self.conn.row_factory = sqlite3.Row
        else:
            self.conn = pymysql.Connect(
                host=self.server,
                port=3306,
                user=self.username,
                passwd=self.password,
                db=self.database,
                charset='utf8')

        cur = self.conn.cursor()
        return cur

    def __ExecQuery(self,sql):
        """Execute a SQL query"""
        if not self.isMSSQL:
            sql = sql.replace("dbo.", "").replace("N'","'")
        cur = self.__GetConnect()
        #print(sql)
        cur.execute(sql)
        resList = cur.fetchall()
        self.conn.close()
        return resList

    def __ExecNonQuery(self,sql):
        """Execute a SQL statement"""
        if not self.isMSSQL:
            sql = sql.replace("dbo.", "").replace("N'","'")
        cur = self.__GetConnect()
        #print(sql)
        cur.execute(sql)
        self.conn.commit()
        self.conn.close()

    def LogMessage(self, msg):
        """log a message into DB for backup"""
        cmd = "INSERT INTO dbo.RawMsg (TimeStamp, RawMsg, FromUser, ToUser, MsgType) VALUES "+\
           "('%s',N'%s','%s','%s', '%s')" % (msg.TimeStamp, msg.RawContent, msg.FromUser, msg.ToUser, msg.MsgType)
        self.__ExecNonQuery(cmd)

        if self.save_to_azuretable:
            json_string = json.dumps([{'time' : msg.TimeStamp.strftime("%Y-%m-%d %H:%M:%S"), \
            'content' : msg.RawContent,'from' : msg.FromUser,'to' : msg.ToUser,'type' : msg.MsgType}], ensure_ascii=False)
            task = Entity()
            task.PartitionKey = msg.TimeStamp.strftime("%Y%m")
            task.RowKey = msg.TimeStamp.strftime("%Y%m%d%H%M%S")
            task.description = json_string
            iRetry = 1
            iRetryMax = 10
            while iRetry <= iRetryMax:#retry for 10 times
                try:
                    self.azuretable_service.insert_entity('robertlograwmsg', task)
                except:
                    task.RowKey =  (msg.TimeStamp + datetime.timedelta(seconds=iRetry)).strftime("%Y%m%d%H%M%S")
                    iRetry += 1
                else:
                    iRetry = iRetryMax + 1
            

    def AppendAction(self, act):
        """log a user action into DB for futhure query"""
        cmdstr = "INSERT INTO dbo.Actions (CreateTime, ActionType, FromUser, ActionDetail, ActionStatus) VALUES "+\
           "('%s','%s','%s',N'%s', '%s')" % (act.TimeStamp, act.Type, act.FromUser, act.Detail, act.Status)
        #print(cmdstr)
        self.__ExecNonQuery(cmdstr)

        if self.save_to_azuretable:
            json_string = json.dumps([{'time' : act.TimeStamp.strftime("%Y-%m-%d %H:%M:%S"),\
             'type' : act.Type, 'from' : act.FromUser, 'detail' : act.Detail, 'status' : act.Status}], ensure_ascii=False)
            task = Entity()
            task.PartitionKey = act.TimeStamp.strftime("%Y%m")
            task.RowKey = act.TimeStamp.strftime("%Y%m%d%H%M%S")
            task.description = json_string
            iRetry = 1
            while iRetry <= 10:#retry for 10 times
                try:
                    self.azuretable_service.insert_entity('robertlogaction', task)
                except:
                    task.RowKey =  (act.TimeStamp + datetime.timedelta(seconds=iRetry)).strftime("%Y%m%d%H%M%S")
                    iRetry += 1
                else:
                    iRetry = 11
    
    def JsonAction2DB(self, msg):

        act = json.loads(msg)
        cmdstr = "INSERT INTO dbo.Actions (CreateTime, ActionType, FromUser, ActionDetail, ActionStatus) VALUES "+\
           "('%s','%s','%s',N'%s', '%s')" % (act[0]['time'], act[0]['type'], act[0]['from'], act[0]['detail'], act[0]['status'])
        self.__ExecNonQuery(cmdstr)

    def GetActionReports(self, num = 30):
        """List all the last # actions"""
        cmd = self.GenSelectTopSQL("FROM dbo.Actions ORDER BY CreateTime DESC", num)
        actList = self.__ExecQuery(cmd)
        retList = []
        for a in actList:
            act = self.LoadActionFromDB(a)
            retList.append(act)

        return retList

    def GetActionFromUser(self, fromUser, num = 1):
        """List all the last # actions"""
        cmd = self.GenSelectTopSQL("FROM dbo.Actions WHERE FromUser = N'{0}' ORDER BY CreateTime DESC".format(fromUser), num)
        actList = self.__ExecQuery(cmd)
        retList = []
        for a in actList:
            act = self.LoadActionFromDB(a)
            retList.append(act)
        
        return retList

    def DeleteLastAction(self):
        """delete the last active item"""
        cmdstr = "update dbo.Actions set ActionStatus = 'Deleted' where ActionID=(select max(ActionID) from dbo.Actions where ActionStatus = 'Active')"
        self.__ExecNonQuery(cmdstr)

    def DeleteAction(self, itemID):
        """delete item with specific ID"""
        cmdstr = "update dbo.Actions set ActionStatus = 'Deleted' where ActionID=(%s)" % itemID
        self.__ExecNonQuery(cmdstr)
    
    def GetLastFallSleep(self):
        return self.GetLastAction('Sleep')

    def GetMsgFromUser(self, fromUser, num = 1):
        """List all the last # message"""
        cmd = self.GenSelectTopSQL("from dbo.RawMsg where FromUser = N'{0}' ORDER BY TimeStamp DESC".format(fromUser), num)
        msgList = self.__ExecQuery(cmd)
        retList = []
        for m in msgList:
            retList.append(self.LoadMsgFromDB(m))
        
        return retList
        
    def GetLastAD(self):
        return self.GetLastAction('AD')

    def GetLastCa(self):
        return self.GetLastAction('EatCa')
    
    def GetLastPill(self):
        return self.GetLastAction('Pills')

    def GetLastAction(self, act_name):
        """List the last AD actions"""
        cmd =  self.GenSelectTopSQL("FROM dbo.Actions Where ActionType = '%s' AND ActionStatus = 'Active' ORDER BY CreateTime DESC" % act_name, 1)
        actList = self.__ExecQuery(cmd)

        if len(actList) <= 0:
            return None

        a = actList[0]
        act = self.LoadActionFromDB(a)

        return act

    def GetActionList(self, act_name, num):
        """List the last AD actions"""
        cmd = self.GenSelectTopSQL("FROM dbo.Actions Where ActionType = '{0}' ORDER BY CreateTime DESC".format(act_name), num)
        actList = self.__ExecQuery(cmd)

        if len(actList) <= 0:
            return None

        retList = []
        for a in actList:
            retList.append(self.LoadActionFromDB(a))
            #print(msg)
        return retList
    
    def GetSleepStatus(self):
        """List the last AD actions"""
        cmd = self.GenSelectTopSQL("FROM dbo.Actions Where ActionStatus = 'Active' AND ( ActionType = 'Sleep' OR ActionType = 'WakeUp') ORDER BY CreateTime DESC", 1)

        actList = self.__ExecQuery(cmd)

        if len(actList) <= 0:
            return None

        a = actList[0]
        act = self.LoadActionFromDB(a)

        return act

    def getdbattr(self, v, attribute_name):
        if self.isMSSQL:
            return v.getattr(attribute_name)
        else:
            return v[attribute_name]

    def LoadActionFromDB(self, a):
        act = Action()
        act.FromUser = self.getdbattr(a, "FromUser").strip()
        act.Status = self.getdbattr(a, "ActionStatus").strip()
        act.Type = self.getdbattr(a, "ActionType").strip()
        act.Detail = self.getdbattr(a, "ActionDetail").strip()
        ct = self.getdbattr(a, "CreateTime")
        pos = ct.find('.')
        if pos >= 0 :
            timestr = ct[:pos].strip()
        else :
            timestr = ct.strip()

        act.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        act.ActionID = self.getdbattr(a, "ActionID")
        return act

    def LoadMsgFromDB(self, m):
        msg = Message()
        msg.FromUser = self.getdbattr(m, "FromUser").strip()
        msg.ToUser = self.getdbattr(m, "ToUser").strip()
        msg.RawContent = self.getdbattr(m, "RawMsg").strip()
        pos = self.getdbattr(m, "TimeStamp").index('.')
        timestr = self.getdbattr(m, "TimeStamp")[:pos].strip()
        msg.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        return msg

    def GetLastNumMsg(self, num = 20):
        """List all the last # actions"""
        cmd = self.GenSelectTopSQL("from dbo.RawMsg",num)
        cmd += " where RawMsg NOT like N'%调试%' ORDER BY TimeStamp DESC"
        actList = self.__ExecQuery(cmd)
        if len(actList) <= 0:
            return None
        
        retList = []
        for m in actList:
            retList.append(self.LoadMsgFromDB(m))
            #print(msg)
        return retList

    def DumpResultToStream(self, sqlcmd, streamWriter):
        cur = self.__GetConnect()
        cur.execute(sqlcmd)

        streamWriter.writerow([d[0] for d in cur.description])
        data = cur.fetchall()
        streamWriter.writerows(data)
        self.conn.close()

    def DumpTableToStream(self, table, streamWriter, orderby_column):
        cmd  = " SELECT * FROM dbo.[{0}] ORDER BY {1}".format(table, orderby_column)
        self.DumpResultToStream(cmd, streamWriter)

    def ImportListToDB(self, table, headers, csv_data):
        cmdTemplate = 'INSERT INTO {0} ( {1} ) VALUES ( "'.format(table, headers) 
        cur = self.__GetConnect()
        for row in csv_data:
            if len(row) == 0:
                continue
            values = "\",\"".join(row)
            cmd = cmdTemplate + values + '")'
            #print(cmd)
            cur.execute( cmd )

        self.conn.commit()
        self.conn.close()

    def GenSelectTopSQL(self, sql_cmd, num):
        if self.isMSSQL:
            return "SELECT TOP {0} * {1}".format(num, sql_cmd)
        else:
            return "SELECT * {0} LIMIT 0,{1}".format(sql_cmd, num)
