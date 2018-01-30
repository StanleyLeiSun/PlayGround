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
        cmd = "INSERT INTO [dbo].[RawMsg] ([TimeStamp], [RawMsg], [FromUser], [ToUser]) VALUES "+\
           "('%s',N'%s','%s','%s')" % (msg.TimeStamp, msg.RawContent, msg.FromUser, msg.ToUser)
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
            act.FromUser = a.FromUser
            act.Status = a.ActionStatus
            act.Type = a.ActionType.strip()
            act.Detail = a.ActionDetail
            act.TimeStamp = datetime.datetime.strptime(a.CreateTime.strip().rstrip('0'), \
            '%Y-%m-%d %H:%M:%S.%f')
            retList.append(act)

        return retList

    
