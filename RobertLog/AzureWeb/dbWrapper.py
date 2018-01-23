import pyodbc
from entityClasses import Message, Action

class RobertLogMSSQL:
    def __init__(self,host,user,pwd,db):
        self.server = host
        self.database = db
        self.username = user
        self.password = pwd
        self.driver= '{ODBC Driver 13 for SQL Server}'
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
           "('%s','%s','%s','%s')" % (msg.TimeStamp, msg.RawMsg, msg.FromUser, msg.ToUser)
        self.ExecNonQuery(cmd)

    def AppendAction(self, act):
        cmd = "INSERT INTO [dbo].[Actions] ([TimeStamp], [ActionType], [FromUser], [ActionDetail], [ActionStatus]) VALUES "+\
           "('%s','%s','%s','%s, %s')" % (act.TimeStamp, act.Type, act.FromUser, act.Detail, act.Status)
        self.ExecNonQuery(cmd)

    
