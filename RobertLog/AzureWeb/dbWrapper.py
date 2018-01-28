import pyodbc
import datetime
from entityClasses import Message, Action

class RobertLogMSSQL:
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

    def ExecQuery(self,sql):
        cur = self.__GetConnect()
        cur.execute(sql)
        resList = cur.fetchall()
        self.conn.close()
        return resList

    def ExecNonQuery(self,sql):
        cur = self.__GetConnect()
        cur.execute(sql)
        self.conn.commit()
        self.conn.close()

    def LogMessage(self, msg):
        cmd = "INSERT INTO [dbo].[RawMsg] ([TimeStamp], [RawMsg], [FromUser], [ToUser]) VALUES "+\
           "('%s','%s','%s','%s')" % (msg.TimeStamp, msg.RawContent, msg.FromUser, msg.ToUser)
        self.ExecNonQuery(cmd)

    def AppendAction(self, act):
        cmdstr = "INSERT INTO [dbo].[Actions] ([CreateTime], [ActionType], [FromUser], [ActionDetail], [ActionStatus]) VALUES "+\
           "('%s','%s','%s','%s', '%s')" % (act.TimeStamp, act.Type, act.FromUser, act.Detail, act.Status)
        #print(cmdstr)
        self.ExecNonQuery(cmdstr)

    def GetActionReports(self, num = 30):
        cmd = "SELECT TOP %s * FROM [dbo].[Actions] ORDER BY CreateTime DESC" % num
        actList = self.ExecQuery(cmd)
        retList = []
        for a in actList:
            act = Action()#TODO
            act.FromUser = a.FromUser
            act.Status = a.ActionStatus
            act.Type = a.ActionType.strip()
            act.Detail = a.ActionDetail
            act.TimeStamp = datetime.datetime.strptime(a.CreateTime.strip().rstrip('0'), '%Y-%m-%d %H:%M:%S.%f')
            retList.append(act)

        return retList

    
