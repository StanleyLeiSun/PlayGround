#coding: utf-8
"""
Key structures
"""
import xml.etree.ElementTree as ET
import datetime
import cn_utility

class Message:
    """Structurlized Message between WeiChat and backend"""

    def __init__(self, msg = None):
        if not msg:
            self.MsgType = "text"
            return

        xml = ET.fromstring(msg)
        self.MsgType=xml.find("MsgType").text
        self.FromUser=xml.find("FromUserName").text
        self.ToUser=xml.find("ToUserName").text
        self.TimeStamp = datetime.datetime.utcnow() + datetime.timedelta(hours=+8)

        if self.MsgType == "text":
            self.RawContent = xml.find("Content").text
        elif self.MsgType == "image":
            self.PicUrl = xml.find("PicUrl").text
            self.MediaId = xml.find("MediaId").text
            self.RawContent = "image:" + self.MediaId
        else:
            pass
        

class Action:
    """Interprete a message to an action"""

    Active = "Active"
    Deleted = "Deleted"

    def __init__(self, msg = None):
        if msg :
            self.message = msg
            self.FromUser =msg.FromUser
            self.Status = "Active"
            self.Type = "UnKnown"
            self.Detail = msg.RawContent
            self.TimeStamp = msg.TimeStamp

    def GenBrief(self):
        """Brief the action as a str"""

        brief = "[{0}] {1} ".format(self.TimeStamp.strftime( "%H:%M"), ActionType.actionNames[self.Type])

        if self.Type in {ActionType.Feed, ActionType.Notes, ActionType.WakeUp, ActionType.SleepTime, ActionType.ComFood, ActionType.ErrStatus}:
            brief += self.Detail
        elif self.Type == ActionType.Poop:
            pass
        elif self.Type == ActionType.AD:
            pass
        elif self.Type == ActionType.UnKnown:
            brief += "可以尝试 '总结' 或 '一周总结' 查看萝卜成长状态。"
        elif self.Type == ActionType.FallSleep:
            tnow = cn_utility.GetNowForUTC8()
            delta_minutes = int((tnow - self.TimeStamp).total_seconds()/60)
            brief += "已经睡了{0}小时{1}分钟".format(int(delta_minutes/60), delta_minutes%60)
        else:
            pass
        return brief


class ActionType:
    """Enum of the types"""

    UnKnown = "UnKnown"
    Feed = "Feed"
    Poop = "Poop"
    AD = "AD"
    Bath = "Bath"
    Reports = "Report"
    WeeklyReports ="WeeklyReports"
    Notes = "Notes"
    Remove = "Remove"
    NoPermission = "NoPermission"
    FallSleep = "Sleep"
    WakeUp = "WakeUp"
    ListImage = "ListImg"
    SleepTime = "SleepTime"
    DebugMsg = "DebugMsg"
    EatCa = "EatCa"
    RemoveSpecific = "RemoveS"
    ComFood = "SupFood"
    ErrStatus = "ErrStatus"
    ComFoodList = "SupFoodList"

    actionNames = {UnKnown:"未知命令", Feed:"喂奶", Poop:"大便", AD:"吃了AD", Bath:"洗澡", \
    Reports:"汇报", WeeklyReports:"一周汇总", Notes:"备注", Remove:"撤销", FallSleep:"睡着了",\
    WakeUp:"睡觉", ListImage:"看照片", SleepTime:"睡着时间", DebugMsg:"DebugMsg", EatCa:"补钙",\
    RemoveSpecific:"删除特定", ComFood:"辅食", ErrStatus:"状态错误", ComFoodList:"辅食食谱"}

class DailyReport:
    def __init__(self, milk_ml, milk_min, milk_num, poop, sleep, date):
        self.milk_ml = milk_ml
        self.milk_min = milk_min
        self.poop = poop
        self.sleep = sleep
        self.milk_num = milk_num
        self.date = date

    
