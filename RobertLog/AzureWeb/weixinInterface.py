# -*- coding: utf-8 -*-
"""
WeiXinInterface
~~~~~~~~~~~~~~~~
Define the interface to WeiChat

    #developer id wx53b8a28638e040d3
    #token xxxxx
    #encoding key gJ3g38Z7NXVSBxarCStIDWS8RIhrzR131lLyOfi7ulZ
"""
import hashlib
import time
import os
import xml.etree.ElementTree as ET
import config
from actionCenter import ActionCenter
from flask import render_template
from flask import request

class WeixinInterface:
    """
    Main class
        >>>callback_get: use to check the authority of the caller
        >>>callback_post: Receive the message and response
    """
    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        self.actCenter = ActionCenter()

    def callback_get(self):
        """Authority the caller"""
        
        signature = request.args.get("signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        echostr = request.args.get("echostr")
        token = config.weichat_token

        stamp_list = [token, timestamp, nonce]
        stamp_list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, stamp_list)
        hashcode = sha1.hexdigest()

        if hashcode == signature:
            return echostr

    def callback_post(self):
        """receive message and do all the works"""

        str_xml = request.data
        xml = ET.fromstring(str_xml)
        fromuser = xml.find("FromUserName").text
        touser = xml.find("ToUserName").text

        ret = self.actCenter.Receive(str_xml)

        if type(ret) == str :  
            return render_template("main_ret.ret",\
                toUser = fromuser, fromUser = touser,\
                createTime = int(time.time()),\
                content = ret)
        elif type(ret) == list:
            return render_template("img_list.ret",\
                toUser = fromuser, fromUser = touser,\
                createTime = int(time.time()),\
                pictures = ret)
