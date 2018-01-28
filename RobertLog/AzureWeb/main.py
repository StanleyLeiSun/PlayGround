#coding=utf-8
from flask import Flask
#from flask import render_template
from weixinInterface import WeixinInterface
from xml import etree
import xml.etree.ElementTree as ET
from dbWrapper import RobertLogMSSQL
from actionCenter import ActionCenter

app = Flask(__name__)

weixin = WeixinInterface()
actCenter = ActionCenter()

ms = RobertLogMSSQL(host="robertlog.database.windows.net",user="rluser",pwd="Xiaoluobo666",db="robertlog")

str_feedcmd_xml =  "<xml><ToUserName><![CDATA[fromUser]]></ToUserName>" +\
        "<FromUserName><![CDATA[toUser]]></FromUserName>" +\
        "<CreateTime>123445</CreateTime>" +\
        "<MsgType><![CDATA[text]]></MsgType>"+\
        "<Content><![CDATA[喂了200]]></Content>"+\
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
  print (actCenter.Receive(str_feedcmd_xml))

def TestReport():
  str_report = str_cmdtemplate_xml.format("今日情况")
  print (actCenter.Receive(str_report))

TestReport()
#TestActions()

@app.route('/')
def hello_world():
  return 'Hello World'

@app.route('/weixin', methods=['GET'])
def weixin_get():
  return weixin.GET()

@app.route('/weixin', methods=['POST'])
def weixin_post():
  return weixin.POST()

if __name__ == '__main__':
  app.run()
