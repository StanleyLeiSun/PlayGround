"""
Key structures
"""
import xml.etree.ElementTree as ET
import datetime

class Message:
    """Structurlized Message between WeiChat and backend"""

    def __init__(self, msg):
        xml = ET.fromstring(msg)
        self.RawContent=xml.find("Content").text
        self.MsgType=xml.find("MsgType").text
        self.FromUser=xml.find("FromUserName").text
        self.ToUser=xml.find("ToUserName").text
        self.TimeStamp = datetime.datetime.utcnow() + datetime.timedelta(hours=+8)

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

        if self.Type in {ActionType.Feed, ActionType.Notes}:
            brief += self.Detail
        elif self.Type == ActionType.Poop:
            pass
        elif self.Type == ActionType.AD:
            pass
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

    actionNames = {UnKnown:"未知", Feed:"喂奶", Poop:"拉屎了", AD:"吃了AD", Bath:"洗澡", Reports:"汇报", WeeklyReports:"一周汇总", Notes:"备注", Remove:"撤销"}
    
