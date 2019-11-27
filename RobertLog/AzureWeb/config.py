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
StoryLineName = "storyline_"
sqlite_db = xml.find("SQLITEDB").text
azuretable_account = xml.find("AzureTableAccount").text
azuretable_key = xml.find("AzureTableKey").text

birthday = datetime.date(2017, 11, 8)


def get_days_to_birth():
    dt = datetime.datetime.utcnow()  + datetime.timedelta(hours=+8)
    return get_days_to_birth(dt)

def get_days_to_birth(dt):
    return (dt.date() - birthday).days + 1

def userId_to_name(id):
    user_mapping = {"ocgSc0eChTDEABMBHJ_urv4lMeCE" : "李菡", \
    "ocgSc0fzGH2Os2cmFYQ58zdDPCWw" : "孙磊", \
    "ocgSc0cpvPB5V7KPdcBSdu0VQvXQ" : "奶奶", \
    "ocgSc0X3el46D3JbN5Brwr0SVrII" : "姥姥", \
    "ocgSc0fIrUDX5iDolCX_D0KBYiGs" : "老爷", \
    "ocgSc0a7I2-DcquxOaN5G43BOSbQ" : "爷爷"}

    return user_mapping.get(id,id)