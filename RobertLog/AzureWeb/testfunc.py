from dbWrapper import RobertLogMSSQL
from actionCenter import ActionCenter
import xml.etree.ElementTree as ET
import config
from cn_utility import num_cn2digital, extract_cn_time
import cn_utility
from flask import render_template, Flask


actCenter = ActionCenter()

ms = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")

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


#app = Flask(__name__)
def TestImageList():
    str_report = str_cmdtemplate_xml.format("看照片")
    imgs = actCenter.Receive(str_report)
    print(render_template("img_list.ret",\
                toUser = "fromuser", fromUser = "touser",\
                createTime = "1234", itemCount = "6", \
                pictures = imgs))


#TestReport()
#TestActions()
#TestDelete()
#TestImageList()

#cn2d = num_cn2digital()
#cn2d.Test()

#ect = extract_cn_time()
#ect.Test()
#times = ect.extract_time_v2("从21:10到03:15，睡了6小时")
#print(times)
#delta = ect.extract_time_delta("从21:10到03:15，睡了6小时")
#print(delta)

#print(config.db_pwd, config.weichat_token)

#cn_utility.listimgfiles("C:\\temp\\", 10)