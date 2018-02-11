import xml.etree.ElementTree as ET

xml = ET.parse('secret.txt')
db_pwd = xml.find("DBPWD").text
weichat_token = xml.find("WeiChatToken").text
db_server = xml.find("DBServer").text
db_user = xml.find("DBUSER").text
ImageRoot = "c:\\image\\"
