#coding: utf-8
from dbWrapper import RobertLogMSSQL
from actionCenter import ActionCenter
import xml.etree.ElementTree as ET
import config
from cn_utility import num_cn2digital, extract_cn_time
import cn_utility
from flask import render_template, Flask
import reporting
import warning
import datetime
import entityClasses


actCenter = ActionCenter()

#ms = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")


str_cmdtemplate_xml =  "<xml><ToUserName><![CDATA[gh_273eb9aee5b4]]></ToUserName>" +\
        "<FromUserName><![CDATA[ocgSc0fzGH2Os2cmFYQ58zdDPCWw]]></FromUserName>" +\
        "<CreateTime>123445</CreateTime>" +\
        "<MsgType><![CDATA[text]]></MsgType>"+\
        "<MsgId><![CDATA[MsgId_fake]]></MsgId>"+\
        "<Content><![CDATA[{0}]]></Content>"+\
        "</xml>"


def TestReport(msg):
    str_report = str_cmdtemplate_xml.format("备注 " + msg)
    print(actCenter.Receive(str_report))

TestReport("萝卜在幼儿园是个小暖男，楼上装修突然有很大噪音后就跑到老师那里拍拍老师然后说：萌萌别怕。")