# -*- coding: utf-8 -*-
"""
Wrapper of the Data Layer operations
https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-2017

"""
import datetime
import pyodbc
import pymysql
from entityClasses import Message, Action

class RobertLogMSSQL:
    """Wrapper of the MSSQL"""
    def __init__(self,host,user,pwd,db, driver = '{SQL Server}'):
        self.server = host
        self.database = db
        self.username = user
        self.password = pwd
        self.driver= driver
        self.isMSSQL = driver == '{SQL Server}'
        self.driver= '{ODBC Driver 17 for SQL Server}'
        #self.driver= '{SQL Server Native Client 11.0}'

    def __GetConnect(self):
        if self.isMSSQL:
            self.conn = pyodbc.connect('DRIVER=' + self.driver +\
            ';PORT=1433;SERVER='+self.server+\
            ';DATABASE='+self.database+\
            ';UID='+self.username+\
            ';PWD='+ self.password)
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
            sql = sql.replace("dbo.", "")
        cur = self.__GetConnect()
        cur.execute(sql)
        resList = cur.fetchall()
        self.conn.close()
        return resList

    def __ExecNonQuery(self,sql):
        """Execute a SQL statement"""
        if not self.isMSSQL:
            sql = sql.replace("dbo.", "")
        cur = self.__GetConnect()
        cur.execute(sql)
        self.conn.commit()
        self.conn.close()

    def LogMessage(self, msg):
        """log a message into DB for backup"""
        cmd = "INSERT INTO dbo.RawMsg (TimeStamp, RawMsg, FromUser, ToUser, MsgType) VALUES "+\
           "('%s',N'%s','%s','%s', '%s')" % (msg.TimeStamp, msg.RawContent, msg.FromUser, msg.ToUser, msg.MsgType)
        self.__ExecNonQuery(cmd)

    def AppendAction(self, act):
        """log a user action into DB for futhure query"""
        cmdstr = "INSERT INTO dbo.Actions (CreateTime, ActionType, FromUser, ActionDetail, ActionStatus) VALUES "+\
           "('%s','%s','%s',N'%s', '%s')" % (act.TimeStamp, act.Type, act.FromUser, act.Detail, act.Status)
        #print(cmdstr)
        self.__ExecNonQuery(cmdstr)

    def GetActionReports(self, num = 30):
        """List all the last # actions"""
        cmd = "SELECT TOP %s * FROM dbo.Actions ORDER BY CreateTime DESC" % num
        actList = self.__ExecQuery(cmd)
        retList = []
        for a in actList:
            act = self.LoadActionFromDB(a)
            retList.append(act)

        return retList

    def GetActionFromUser(self, fromUser, num = 1):
        """List all the last # actions"""
        cmd = "SELECT TOP {0} * FROM dbo.Actions WHERE FromUser = N'{1}' ORDER BY CreateTime DESC".format(num, fromUser)
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
        cmd = "select top {0} * from dbo.RawMsg where FromUser = N'{1}' ORDER BY TimeStamp DESC".format(num, fromUser)
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
        cmd = "SELECT TOP 1 * FROM dbo.Actions Where ActionType = '%s' AND ActionStatus = 'Active' ORDER BY CreateTime DESC" % act_name
        actList = self.__ExecQuery(cmd)

        if len(actList) <= 0:
            return None

        a = actList[0]
        act = self.LoadActionFromDB(a)

        return act

    def GetActionList(self, act_name, num):
        """List the last AD actions"""
        cmd = "SELECT TOP {0} * FROM dbo.Actions Where ActionType = '{1}' ORDER BY CreateTime DESC".format(num, act_name)
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
        cmd = "SELECT TOP 1 * FROM dbo.Actions Where ActionStatus = 'Active' AND ( ActionType = 'Sleep' OR ActionType = 'WakeUp') ORDER BY CreateTime DESC"

        actList = self.__ExecQuery(cmd)

        if len(actList) <= 0:
            return None

        a = actList[0]
        act = self.LoadActionFromDB(a)

        return act

    def LoadActionFromDB(self, a):
        act = Action()
        act.FromUser = a.FromUser.strip()
        act.Status = a.ActionStatus.strip()
        act.Type = a.ActionType.strip()
        act.Detail = a.ActionDetail.strip()
        pos = a.CreateTime.index('.')
        timestr = a.CreateTime[:pos].strip()
        act.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        act.ActionID = a.ActionID
        return act

    def LoadMsgFromDB(self, m):
        msg = Message()
        msg.FromUser = m.FromUser.strip()
        msg.ToUser = m.ToUser.strip()
        msg.RawContent = m.RawMsg.strip()
        pos = m.TimeStamp.index('.')
        timestr = m.TimeStamp[:pos].strip()
        msg.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        return msg

    def GetLastNumMsg(self, num = 20):
        """List all the last # actions"""
        cmd = "select top %s * from dbo.RawMsg" % num 
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

        #streamWriter.writerow([d[0] for d in cur.description])
        streamWriter.writerows(cur.fetchall())
        self.conn.close()

    def DumpTableToStream(self, table, streamWriter):
        cmd  = "SELECT * FROM dbo.[{0}]".format(table)
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
