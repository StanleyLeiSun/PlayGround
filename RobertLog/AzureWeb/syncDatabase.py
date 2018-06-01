import pyodbc
import csv
from dbWrapper import RobertLogMSSQL
import config
from sys import argv

if __name__ == '__main__':
    if argv[1] == "export":
        exportDatabase()
    elif argv[1] == "import":
        importDatabase()
    elif
        print("invalid argument, try export or import")

    
def importDatabase():
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")
    with open("rawmsg.csv", 'r') as cvsin:
        fRawMsg = csv.reader(cvsin, delimiter=',', quotechar='"')
        rlSQL.ImportListToDB("RawMsg",
            "MsgID, TimeStamp, RawMsg, FromUser, ToUser, MsgType",
            fRawMsg)

    with open("actions.csv", 'w') as csvout:
        fActions = csv.writer(csvout)
        rlSQL.ImportListToDB("Actions", 
            "ActionID, CreateTime, ActionType, FromeUser, ActionDetail, ActionStatus", 
            fActions)

def exportDatabase():
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")
    with open("rawmsg.csv", 'w') as csvout:
        fRawMsg = csv.writer(csvout)
        rlSQL.DumpTableToStream("RawMsg", fRawMsg)

    with open("actions.csv", 'w') as csvout:
        fActions = csv.writer(csvout)
        rlSQL.DumpTableToStream("Actions", fActions)
