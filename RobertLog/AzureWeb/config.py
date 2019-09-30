import xml.etree.ElementTree as ET
import datetime
import os

xml = ''

if os.path.exists('secret.txt'):
    xml = ET.parse('secret.txt')
else:
    xml = ET.parse(r'/conf/secret.txt')

db_pwd = xml.find("DBPWD").text
weichat_token = xml.find("WeiChatToken").text
db_server = xml.find("DBServer").text
db_user = xml.find("DBUSER").text
ImageRoot = "c:\\image\\"
sqlite_db = xml.find("SQLITEDB").text
azuretable_account = xml.find("AzureTableAccount").text
azuretable_key = xml.find("AzureTableKey").text

birthday = datetime.date(2017, 11, 8)


def get_days_to_birth():
    dt = datetime.datetime.utcnow()  + datetime.timedelta(hours=+8)
    return get_days_to_birth(dt)

def get_days_to_birth(dt):
    return (dt.date() - birthday).days + 1