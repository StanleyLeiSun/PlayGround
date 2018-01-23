from flask import Flask
#from flask import render_template
from weixinInterface import WeixinInterface
from xml import etree
import xml.etree.ElementTree as ET

app = Flask(__name__)

weixin = WeixinInterface()

@app.route('/')
def hello_world():
  str_xml =  "<xml><ToUserName><![CDATA[fromUser]]></ToUserName>" +\
        "<FromUserName><![CDATA[toUser]]></FromUserName>" +\
        "<CreateTime>123445</CreateTime>" +\
        "<MsgType><![CDATA[text]]></MsgType>"+\
        "<Content><![CDATA[content]]></Content>"+\
        "</xml>"
  xml = ET.fromstring(str_xml)
  content=xml.find("Content").text
  msgType=xml.find("MsgType").text
  fromUser=xml.find("FromUserName").text
  toUser=xml.find("ToUserName").text
  return content

@app.route('/weixin', methods=['GET'])
def weixin_get():
  return weixin.GET()

@app.route('/weixin', methods=['POST'])
def weixin_post():
  return weixin.POST()

if __name__ == '__main__':
  app.run()
