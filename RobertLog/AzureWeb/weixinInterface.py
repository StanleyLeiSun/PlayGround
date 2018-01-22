
import hashlib
#import web
from flask import request
import lxml
import time
import os
import json
from lxml import etree

class WeixinInterface:

    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        #self.render = web.template.render(self.templates_root)

    def GET(self):
        #获取输入参数
        signature = request.args.get("signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        echostr = request.args.get("echostr")
        #自己的token
        token="stansun" #这里改写你在微信公众平台里输入的token 
        #encoding key gJ3g38Z7NXVSBxarCStIDWS8RIhrzR131lLyOfi7ulZ
        #developer id wx53b8a28638e040d3
        #字典序排序
        list=[token,timestamp,nonce]
        list.sort()
        sha1=hashlib.sha1()
        map(sha1.update,list)
        hashcode=sha1.hexdigest()
        #sha1加密算法        
 
        #如果是来自微信的请求，则回复echostr
        if hashcode == signature:
            return echostr
    
    # def render_return(toUser,fromUser,createTime,content):
    #     <xml>
    #     <ToUserName><![CDATA[$toUser]]></ToUserName>
    #     <FromUserName><![CDATA[$fromUser]]></FromUserName>
    #     <CreateTime>$createTime</CreateTime>
    #     <MsgType><![CDATA[text]]></MsgType>
    #     <Content><![CDATA[$content]]></Content>
    #     </xml>

    def POST(self):        
        str_xml = request.data #获得post来的数据 or request.values
        xml = etree.fromstring(str_xml)#进行XML解析
        content=xml.find("Content").text#获得用户所输入的内容
        msgType=xml.find("MsgType").text
        fromUser=xml.find("FromUserName").text
        toUser=xml.find("ToUserName").text
        return str_xml
        #return self.render.reply_text(fromUser,toUser,int(time.time()),u"我现在还在开发中，还没有什么功能，您刚才说的是："+content)