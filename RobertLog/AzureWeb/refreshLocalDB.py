from dbWrapper import RobertLogMSSQL
import config
import cn_utility
import datetime
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
   
if __name__ == '__main__':
    
    now = cn_utility.GetNowForUTC8()
    partition = now.strftime("%Y%m")
    enumPartition(partition)

    partition = (now.replace(day=1)  - datetime.timedelta(days=1)).strftime("%Y%m")
    enumPartition(partition)
