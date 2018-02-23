import xml.etree.ElementTree as ET
import datetime

xml = ET.parse('secret.txt')
db_pwd = xml.find("DBPWD").text
weichat_token = xml.find("WeiChatToken").text
db_server = xml.find("DBServer").text
db_user = xml.find("DBUSER").text
ImageRoot = "c:\\image\\"

birthday = datetime.date(2017, 11, 8)


def get_days_to_birth():
    n = datetime.datetime.utcnow()  + datetime.timedelta(hours=+8)
    return (n.date() - birthday).days + 1
