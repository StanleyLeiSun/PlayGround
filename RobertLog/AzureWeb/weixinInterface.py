import hashlib
from flask import render_template
from flask import request
import time
import os
import json
from xml import etree
import xml.etree.ElementTree as ET

class WeixinInterface:

    # def __init__(self):
    #     self.app_root = os.path.dirname(__file__)
    #     self.templates_root = os.path.join(self.app_root, 'templates')
    #     #self.render = web.template.render(self.templates_root)

    def GET(self):
        signature = request.args.get("signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        echostr = request.args.get("echostr")
        token="stansun"
        #encoding key gJ3g38Z7NXVSBxarCStIDWS8RIhrzR131lLyOfi7ulZ
        #developer id wx53b8a28638e040d3

        list=[token,timestamp,nonce]
        list.sort()
        sha1=hashlib.sha1()
        map(sha1.update,list)
        hashcode=sha1.hexdigest()

        if hashcode == signature:
            return echostr
    
    # def POST(self):
    #     return "<xml><ToUserName><![CDATA[fromUser]]></ToUserName>" +\
    #     "<FromUserName><![CDATA[toUser]]></FromUserName>" +\
    #     "<CreateTime>123445</CreateTime>" +\
    #     "<MsgType><![CDATA[text]]></MsgType>"+\
    #     "<Content><![CDATA["+request.data+"]]></Content>"+\
    #     "</xml>"

    def POST(self):
        #return render_template("main_ret.ret",\
        #    toUser = "fromUser", fromUser = "toUser",\
        #    createTime = int(time.time()),\
        #    content = u"Simply copy:"+content)

        str_xml = request.data
        xml = ET.fromstring(str_xml)
        content=xml.find("Content").text
        msgType=xml.find("MsgType").text
        fromUser=xml.find("FromUserName").text
        toUser=xml.find("ToUserName").text
        return render_template("main_ret.ret",\
            toUser = fromUser, fromUser = toUser,\
            createTime = int(time.time()),\
            content = u"Simply copy:"+content)
