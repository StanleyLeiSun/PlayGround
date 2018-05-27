import pyodbc
import csv
from dbWrapper import RobertLogMSSQL
import config

if __name__ == '__main__':
    
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")
    with open("rawmsg.csv", 'w') as csvout:
        fRawMsg = csv.writer(csvout)
        rlSQL.DumpTableToStream("RawMsg", fRawMsg)

    with open("actions.csv", 'w') as csvout:
        fActions = csv.writer(csvout)
        rlSQL.DumpTableToStream("Actions", fActions)