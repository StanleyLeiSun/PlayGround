from dbWrapper import RobertLogMSSQL
from actionCenter import ActionCenter
import xml.etree.ElementTree as ET
import config
from cn_utility import num_cn2digital, extract_cn_time


actCenter = ActionCenter()

ms = RobertLogMSSQL(host="robertlog.database.windows.net",user="rluser",pwd="Xiaoluobo666",db="robertlog")

str_feedcmd_xml =  "<xml><ToUserName><![CDATA[fromUser]]></ToUserName>" +\
        "<FromUserName><![CDATA[toUser]]></FromUserName>" +\
        "<CreateTime>123445</CreateTime>" +\
        "<MsgType><![CDATA[text]]></MsgType>"+\
        "<Content><![CDATA[两点半喂了200]]></Content>"+\
        "</xml>"

str_cmdtemplate_xml =  "<xml><ToUserName><![CDATA[fromUser]]></ToUserName>" +\
        "<FromUserName><![CDATA[toUser]]></FromUserName>" +\
        "<CreateTime>123445</CreateTime>" +\
        "<MsgType><![CDATA[text]]></MsgType>"+\
        "<Content><![CDATA[{0}]]></Content>"+\
        "</xml>"

def AdhocTest():
  ms.ExecNonQuery("INSERT INTO [dbo].[RawMsg] ([TimeStamp], [RawMsg], [FromUser], [ToUser]) VALUES "+\
           "('1993','Msg1','FromUser','ToUser')" )

  
  xml = ET.fromstring(str_feedcmd_xml)
  content=xml.find("Content").text
  msgType=xml.find("MsgType").text
  fromUser=xml.find("FromUserName").text
  toUser=xml.find("ToUserName").text

def TestActions():
    print(actCenter.Receive(str_feedcmd_xml))

def TestReport():
    str_report = str_cmdtemplate_xml.format("今日情况")
    print(actCenter.Receive(str_report))
    str_report = str_cmdtemplate_xml.format("一周总结")
    print(actCenter.Receive(str_report))

def TestDelete():
    str_report = str_cmdtemplate_xml.format("撤销")
    print(actCenter.Receive(str_report))

#TestReport()
#TestActions()
#TestDelete()

#cn2d = num_cn2digital()
#cn2d.Test()

#ect = extract_cn_time()
#ect.Test()
#times = ect.extract_time_v2("从21:10到03:15，睡了6小时")
#print(times)
#print(config.db_pwd, config.weichat_token)