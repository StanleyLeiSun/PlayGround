import xml.etree.ElementTree as ET
import datetime

class Message:
    
    def __init__(self, msg):
        xml = ET.fromstring(msg)
        self.RawContent=xml.find("Content").text
        self.MsgType=xml.find("MsgType").text
        self.FromUser=xml.find("FromUserName").text
        self.ToUser=xml.find("ToUserName").text
        self.TimeStamp = datetime.datetime.utcnow()


class Action:

    Active = "Active"
    Deleted = "Deleted"

    def __init__(self, msg):
        self.message = msg
        self.FromUser = msg.FromUser
        self.Status = "Active"
        self.Type = "UnKnown"
        self.Detail = msg.RawContent
        self.TimeStamp = msg.TimeStamp

    def GenBrief(self):
        brief = "[{0}] [{1}] ".format(self.TimeStamp, self.ActionType)

        if self.Type == ActionType.Feed:
            brief += self.Detail
        elif self.Type == ActionType.Poop:
            pass
        elif self.Type == ActionType.AD:
            pass
        else:
            pass
        return brief


class ActionType :
    UnKnown = "UnKnown"
    Feed = "Feed"
    Poop = "Poop"
    AD = "AD"
    Bath = "Bath"
    Reports = "Report"

