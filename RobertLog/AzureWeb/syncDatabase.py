import pyodbc
import csv
from dbWrapper import RobertLogMSSQL
import config
from sys import argv

def importDatabase():
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")
    with open("rawmsg.csv", 'r', encoding='utf-8') as cvsin:
        fRawMsg = csv.reader(cvsin, delimiter='\t', quotechar='"')
        rlSQL.ImportListToDB("RawMsg",
            "MsgID, TimeStamp, RawMsg, FromUser, ToUser, MsgType",
            fRawMsg)
        print(fRawMsg.line_num)

    with open("actions.csv", 'r', encoding='utf-8') as cvsin:
        fActions = csv.reader(cvsin, delimiter='\t', quotechar='"')
        rlSQL.ImportListToDB("Actions", 
            "ActionID, CreateTime, ActionType, FromUser, ActionDetail, ActionStatus", 
            fActions)
        print(fActions.line_num)

def exportDatabase():
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")
    with open("rawmsg.csv", 'w', encoding='utf-8') as csvout:
        fRawMsg = csv.writer(csvout, delimiter='\t', quotechar='"')
        rlSQL.DumpTableToStream("RawMsg", fRawMsg)

    with open("actions.csv", 'w', encoding='utf-8') as csvout:
        fActions = csv.writer(csvout, delimiter='\t', quotechar='"')
        rlSQL.DumpTableToStream("Actions", fActions)

if __name__ == '__main__':
    if argv[1] == "export":
        exportDatabase()
    elif argv[1] == "import":
        importDatabase()
    else:
        print("invalid argument, try export or import")