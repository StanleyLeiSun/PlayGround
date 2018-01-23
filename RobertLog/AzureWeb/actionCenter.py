from entityClasses import Message, Action, ActionType
from dbWrapper import RobertLogMSSQL

class ActionCenter:

    #SQL
    rlSQL = RobertLogMSSQL(host="robertlog.database.windows.net",user="rluser",pwd="Xiaoluobo666",db="robertlog")

    #Action List
    FeedKeywords = {u"吃了",u"喂了", u"喂奶", u"吃奶"}
    ReportsKeywords = {u"报告", u"总结", u"情况"}
    def Receive(self, raw_str):
        
        msg = Message(raw_str)
        self.rlSQL.LogMessage(msg)
        
        action = DetectAction(msg)
        if action.Status not in {ActionType.UnKnown, ActionType.Reports} :
            self.rlSQL.AppendAction(action)
        else:
            pass
    
    def check_strList(str, listStr):
        for s in listStr:
            if str.find(s) >= 0 :
                return True
        return False

    def DetectAction(self, msg):
        action = Action(msg)
        if check_strList(msg.RawContent, FeedKeywords):
            #feed
            action.Type = ActionType.Feed
            action.Status = Action.Active
        elif check_strList(msg.RawContent, ReportsKeywords):
            #reports
            action.Type = ActionType.Reports
            action.Status = Action.Active
        else:
            action.Type = ActionType.UnKnown
        
        return action
    
    def GenResponse(self, action)
        response = "Please repeat"
        
        if action.Type == ActionType.Feed:
            response = "Got it, he got {0}mL at {1}".format(action.Detail, action.TimeStamp)
        elif: action.Type == ActionType.Reports:
            pass

        return response 




