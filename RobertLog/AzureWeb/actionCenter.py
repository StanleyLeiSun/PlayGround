from entityClasses import Message, Action, ActionType
from dbWrapper import RobertLogMSSQL
import re

class ActionCenter:

    #SQL
    rlSQL = RobertLogMSSQL(host="robertlog.database.windows.net",user="rluser",pwd="Xiaoluobo666",db="robertlog")

    #Action List
    FeedKeywords = {u"吃了",u"喂了", u"喂奶", u"吃奶"}
    ReportsKeywords = {u"报告", u"总结", u"情况"}
    mLKeywords = {u"ml",u"毫升"}
    MinKeywords = {u"分钟", u"一会"}
    ADKeywords = {u"AD"}
    PoopKeywords = {u"拉屎"}
    BathKeywords = {u"洗澡"}

    def check_strList(self, str, listStr):
        for s in listStr:
            if str.find(s) >= 0 :
                return True
        return False

    def DetectAction(self, msg):
        action = Action(msg)
        if self.check_strList(msg.RawContent, self.FeedKeywords):
            #feed
            action.Type = ActionType.Feed
            action.Status = Action.Active
            nums = re.findall(r"\d+",action.message.RawContent)
            if len(nums) > 0:
                if self.check_strList(msg.RawContent, self.MinKeywords):
                    action.Detail = "母乳:" + nums[0] + u"分钟"
                else:
                    action.Detail = "奶瓶:" + nums[0] + "mL"

        elif self.check_strList(msg.RawContent, self.ReportsKeywords):
            #reports
            action.Type = ActionType.Reports
            action.Status = Action.Active
        elif self.check_strList(msg.RawContent, self.ADKeywords):
            action.Type = ActionType.AD
        elif self.check_strList(msg.RawContent, self.PoopKeywords):
            action.Type = ActionType.Poop
        elif self.check_strList(msg.RawContent, self.BathKeywords):
            action.Type = ActionType.Bath
        else:
            action.Type = ActionType.UnKnown
        
        return action
    
    def GenResponse(self, action):
        response = "Please repeat"
        
        if action.Type == ActionType.Feed:
            response = "Got it, he got {0} at {1}".format(action.Detail, action.TimeStamp)
        elif action.Type == ActionType.Reports:
            response = "Here is the list \n"
            actions = self.rlSQL.GetActionReports()
            for a in actions:
                if a.Type not in {ActionType.UnKnown, ActionType.Reports} :
                    response += a.GenBrief()
                    response += "\n"
        
        else:
            response = action.GenBrief()

        return response 

    def Receive(self, raw_str):
        msg = Message(raw_str)
        self.rlSQL.LogMessage(msg)
        
        action = self.DetectAction(msg)
        if action.Type not in {ActionType.UnKnown, ActionType.Reports} :
            self.rlSQL.AppendAction(action)
        else:
            pass
        
        return self.GenResponse(action)
    


