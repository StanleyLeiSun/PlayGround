from dbWrapper import RobertLogMSSQL
import config
import cn_utility
import datetime
import csv
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity

rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")

azuretable_service = TableService( \
            account_name=config.azuretable_account, account_key=config.azuretable_key)

def enumPartition(partition):
    print("Going to enum pation:%s"%partition)
    actions = azuretable_service.query_entities('robertlogaction', filter="PartitionKey eq '%s'"%partition, select='description')
    for act in actions:
        rlSQL.JsonAction2DB(act.description)

def refreshDB():
    now = cn_utility.GetNowForUTC8()
    partition = now.strftime("%Y%m")
    enumPartition(partition)

    partition = (now.replace(day=1)  - datetime.timedelta(days=1)).strftime("%Y%m")
    enumPartition(partition)


def dumpToLocal(table):
    month_cursor = cn_utility.GetNowForUTC8()
    skipped = 3
    with open( table + ".csv", 'w', encoding='utf-8') as csvout:
        fOut = csv.writer(csvout, delimiter='\t', quoting = csv.QUOTE_NONE, quotechar='')
        while skipped > 0:
            
            partition = month_cursor.strftime("%Y%m")
            contents = azuretable_service.query_entities('robertlog'+table, filter="PartitionKey eq '%s'"%partition, select='description')
            
            sum = 0
            for c in contents :
                fOut.writerow(c.description)
                sum+=1
            if sum == 0 :
                skipped = skipped - 1
            
            month_cursor = month_cursor.replace(day=1)  - datetime.timedelta(days=1)

if __name__ == '__main__':
    #refreshDB()
    dumpToLocal("action")
    dumpToLocal("rawmsg")
    
