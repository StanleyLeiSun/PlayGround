# -*- coding: utf-8 -*-
"""
Wrapper of the Data Layer operations
"""
import datetime
import pyodbc
from entityClasses import Message, Action

class RobertLogMSSQL:
    """Wrapper of the MSSQL"""
    def __init__(self,host,user,pwd,db):
        self.server = host
        self.database = db
        self.username = user
        self.password = pwd
        self.driver= '{SQL Server}'
        #self.driver= '{ODBC Driver 13 for SQL Server}'
        #self.driver= '{SQL Server Native Client 11.0}'

    def __GetConnect(self):
        self.conn = pyodbc.connect('DRIVER=' + self.driver +\
        ';PORT=1433;SERVER='+self.server+\
        ';DATABASE='+self.database+\
        ';UID='+self.username+\
        ';PWD='+ self.password)
        cur = self.conn.cursor()
        return cur

    def __ExecQuery(self,sql):
        """Execute a SQL query"""
        cur = self.__GetConnect()
        cur.execute(sql)
        resList = cur.fetchall()
        self.conn.close()
        return resList

    def __ExecNonQuery(self,sql):
        """Execute a SQL statement"""
        cur = self.__GetConnect()
        cur.execute(sql)
        self.conn.commit()
        self.conn.close()

    def LogMessage(self, msg):
        """log a message into DB for backup"""
        cmd = "INSERT INTO [dbo].[RawMsg] ([TimeStamp], [RawMsg], [FromUser], [ToUser], [MsgType]) VALUES "+\
           "('%s',N'%s','%s','%s', '%s')" % (msg.TimeStamp, msg.RawContent, msg.FromUser, msg.ToUser, msg.MsgType)
        self.__ExecNonQuery(cmd)

    def AppendAction(self, act):
        """log a user action into DB for futhure query"""
        cmdstr = "INSERT INTO [dbo].[Actions] ([CreateTime], [ActionType], [FromUser], [ActionDetail], [ActionStatus]) VALUES "+\
           "('%s','%s','%s',N'%s', '%s')" % (act.TimeStamp, act.Type, act.FromUser, act.Detail, act.Status)
        #print(cmdstr)
        self.__ExecNonQuery(cmdstr)

    def GetActionReports(self, num = 30):
        """List all the last # actions"""
        cmd = "SELECT TOP %s * FROM [dbo].[Actions] ORDER BY CreateTime DESC" % num
        actList = self.__ExecQuery(cmd)
        retList = []
        for a in actList:
            act = Action()
            act.FromUser = a.FromUser.strip()
            act.Status = a.ActionStatus.strip()
            act.Type = a.ActionType.strip()
            act.Detail = a.ActionDetail.strip()
            pos = a.CreateTime.index('.')
            timestr = a.CreateTime[:pos].strip()
            act.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
            retList.append(act)

        return retList

    def DeleteLastAction(self, itemID = 0, lastNum = 1):
        """delete item TODO support delete a specific item"""
        cmdstr = "update dbo.Actions set ActionStatus = 'Deleted' where ActionID=(select max(ActionID) from dbo.Actions where ActionStatus = 'Active')"
        self.__ExecNonQuery(cmdstr)
    
    def GetLastFallSleep(self):
        """List all the last # actions"""
        cmd = "select top 1 * from dbo.RawMsg where RawMsg like N'%睡着%' ORDER BY TimeStamp DESC"
        actList = self.__ExecQuery(cmd)
        if len(actList) <= 0:
            return None
        
        msg = Message()
        msg.FromUser = actList[0].FromUser.strip()
        msg.ToUser = actList[0].ToUser.strip()
        msg.RawContent = actList[0].RawMsg.strip()
        pos = actList[0].TimeStamp.index('.')
        timestr = actList[0].TimeStamp[:pos].strip()
        msg.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        return msg

    def GetLastAD(self):
        """List the last AD actions"""
        cmd = "SELECT TOP 1 * FROM [dbo].[Actions] Where ActionType = 'AD' ORDER BY CreateTime DESC"
        actList = self.__ExecQuery(cmd)
        a = actList[0]
        act = Action()
        act.FromUser = a.FromUser.strip()
        act.Status = a.ActionStatus.strip()
        act.Type = a.ActionType.strip()
        act.Detail = a.ActionDetail.strip()
        pos = a.CreateTime.index('.')
        timestr = a.CreateTime[:pos].strip()
        act.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')

        return act

    def GetLastNumMsg(self, num = 20):
        """List all the last # actions"""
        cmd = "select top %s * from dbo.RawMsg" % num 
        cmd += " where RawMsg NOT like N'%调试%' ORDER BY TimeStamp DESC"
        actList = self.__ExecQuery(cmd)
        if len(actList) <= 0:
            return None
        
        retList = []
        for m in actList:
            msg = Message()
            msg.FromUser = m.FromUser.strip()
            msg.ToUser = m.ToUser.strip()
            msg.RawContent = m.RawMsg.strip()
            pos = m.TimeStamp.index('.')
            timestr = m.TimeStamp[:pos].strip()
            msg.TimeStamp = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
            retList.append(msg)
            #print(msg)
        return retList