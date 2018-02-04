from entityClasses import Message, Action, ActionType
from dbWrapper import RobertLogMSSQL
from cn_utility import num_cn2digital, extract_cn_time
import re
import datetime

class ActionCenter:

    #SQL
    rlSQL = RobertLogMSSQL(host="robertlog.database.windows.net",user="rluser",pwd="Xiaoluobo666",db="robertlog")

    #Action List
    FeedKeywords = {u"吃了",u"喂了", u"喂奶", u"吃奶"}
    ReportsKeywords = {u"报告", u"总结", u"情况"}
    mLKeywords = {u"ml",u"毫升"}
    MinKeywords = {u"分钟", u"一会"}
    ADKeywords = {u"AD",u"吃药"}
    PoopKeywords = {u"拉屎",u"大便", }
    BathKeywords = {u"洗澡"}

    def check_strList(self, str, listStr):
        for s in listStr:
            if str.find(s) >= 0 :
                return True
        return False

    def DetectAction(self, msg):
        action = Action(msg)
        num2d = num_cn2digital()
        ect = extract_cn_time()
        content = num2d.replace_cn_digital(msg.RawContent)
        t = ect.extract_time(content)
        if t is not None and len(t) > 0:
            action.TimeStamp = t[0]
            content = ect.remove_time(content)

        if self.check_strList(content, self.FeedKeywords):
            #feed
            action.Type = ActionType.Feed
            action.Status = Action.Active
            nums = re.findall(r"\d+",content)
            if len(nums) > 0:
                if self.check_strList(content, self.MinKeywords):
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
        response = "抱歉没听懂."
        
        if action.Type == ActionType.Feed:
            response = "收到,萝卜在{1}吃了{0}".format(action.Detail, action.TimeStamp.strftime( "%H:%M"))
        elif action.Type == ActionType.Reports:
            response = "统计结果: \n"
            cur = datetime.datetime.utcnow() + datetime.timedelta(days=2)
            actions = self.rlSQL.GetActionReports(20)
            for a in actions:
                if a.Type not in {ActionType.UnKnown, ActionType.Reports} :
                    if a.TimeStamp.day != cur.day:
                        cur = a.TimeStamp
                        response += "{0}日记录:\n".format(cur.strftime("%m-%d")) 
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
    


