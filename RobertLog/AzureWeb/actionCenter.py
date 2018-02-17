# -*- coding: utf-8 -*-
from entityClasses import Message, Action, ActionType
from dbWrapper import RobertLogMSSQL
from cn_utility import num_cn2digital, extract_cn_time
import re
import datetime
import config
import urllib
import config
import cn_utility

class ActionCenter:

    #SQL
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")

    #Action List
    FeedKeywords = {u"吃了",u"喂了", u"喂奶", u"吃奶"}
    ReportsKeywords = {u"报告", u"总结", u"情况"}
    WeeklyReportsKeywords = {u"一周报告", u"一周总结", u"一周情况", u"本周总结"}
    NotesKeywords = {u"备注", u"笔记"}
    mLKeywords = {u"ml",u"毫升"}
    MinKeywords = {u"分钟"}
    ADKeywords = {u"AD",u"吃药", u"ad",u"喂药"}
    PoopKeywords = {u"拉屎",u"大便", }
    BathKeywords = {u"洗澡"}
    RemoveKeywords = {u"撤销", u"删除"}
    FallSleepKeywords = {u"睡着", u"睡觉"}
    WakeUpKeywords = {u"醒了", u"睡醒"}
    ListImageKeywords = {u"看照片"}
    ListSleepTimeKeywords = {u"几点睡",u"睡多久", u"睡了多久"}
    DebugMsgKeywords = {u"调试消息"}

    users_can_write = {"ocgSc0eChTDEABMBHJ_urv4lMeCE", "ocgSc0fzGH2Os2cmFYQ58zdDPCWw", \
    "ocgSc0cpvPB5V7KPdcBSdu0VQvXQ", \
    "ocgSc0X3el46D3JbN5Brwr0SVrII", \
    "ocgSc0fIrUDX5iDolCX_D0KBYiGs"} #stan, hanhan, huaiyan, zhangxin, lishu

    user_mapping = {"ocgSc0eChTDEABMBHJ_urv4lMeCE" : "stan", \
    "ocgSc0fzGH2Os2cmFYQ58zdDPCWw" : "Hanhan", \
    "ocgSc0cpvPB5V7KPdcBSdu0VQvXQ" : "Huaiyan", \
    "ocgSc0X3el46D3JbN5Brwr0SVrII" : "ZhangXin", \
    "ocgSc0fIrUDX5iDolCX_D0KBYiGs" : "LiShu"}
    
    actiontype_skip_log = {ActionType.UnKnown, ActionType.Reports, ActionType.WeeklyReports,\
     ActionType.Remove, ActionType.NoPermission, ActionType.FallSleep, ActionType.ListImage, \
     ActionType.SleepTime, ActionType.DebugMsg}

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

        if self.check_strList(msg.RawContent, self.NotesKeywords):
            action.Type = ActionType.Notes
            action.Detail = msg.RawContent
            for k in self.NotesKeywords:
                action.Detail = action.Detail.lstrip(k)
        elif self.check_strList(msg.RawContent, self.ListSleepTimeKeywords):
            action.Type = ActionType.SleepTime
            self.get_latest_sleep(action, num2d, ect)
        elif self.check_strList(msg.RawContent, self.ADKeywords):
            action.Type = ActionType.AD
        elif self.check_strList(content, self.FeedKeywords):
            #feed
            action.Type = ActionType.Feed
            action.Status = Action.Active
            nums = re.findall(r"\d+",content)
            if len(nums) > 0:
                if self.check_strList(content, self.MinKeywords):
                    action.Detail = "母乳:" + nums[0] + u"分钟"
                else:
                    action.Detail = "奶瓶:" + nums[0] + "mL"
        elif self.check_strList(msg.RawContent, self.WeeklyReportsKeywords):
            action.Type = ActionType.WeeklyReports
        elif self.check_strList(msg.RawContent, self.RemoveKeywords):
            action.Type = ActionType.Remove
        elif self.check_strList(msg.RawContent, self.ReportsKeywords):
            #reports
            action.Type = ActionType.Reports
            action.Status = Action.Active
        elif self.check_strList(msg.RawContent, self.PoopKeywords):
            action.Type = ActionType.Poop
        elif self.check_strList(msg.RawContent, self.BathKeywords):
            action.Type = ActionType.Bath
        elif self.check_strList(msg.RawContent, self.FallSleepKeywords):
            action.Type = ActionType.FallSleep
        elif self.check_strList(msg.RawContent, self.WakeUpKeywords):
            action.Type = ActionType.WakeUp
            self.get_latest_sleep(action, num2d, ect)
        elif self.check_strList(msg.RawContent, self.DebugMsgKeywords):
            action.Type = ActionType.DebugMsg
        elif self.check_strList(msg.RawContent, self.ListImageKeywords):
            action.Type = ActionType.ListImage
            files = cn_utility.listimgfiles(config.ImageRoot, 7)
            action.ImageList = []
            for f in files:
                action.ImageList.append((f[5:16], \
                "http://stansunlog.eastasia.cloudapp.azure.com/robert_image?name="+f))
        else:
            action.Type = ActionType.UnKnown
        
        if action.FromUser not in self.users_can_write and action.Type not in \
            {ActionType.Reports, ActionType.WeeklyReports, ActionType.ListImage}:
            action.Type = ActionType.NoPermission

        return action

    def get_latest_sleep(self, action, num2d, ect):
        sleep = self.rlSQL.GetLastFallSleep()
        if not sleep:
            action.Type = ActionType.UnKnown
        else:
            #check previous time
            pre_content = num2d.replace_cn_digital(sleep.RawContent)
            sleep_t = ect.extract_time(pre_content)
            if sleep_t is None or len(sleep_t) <= 0:
                sleep_t = sleep.TimeStamp
            else:
                sleep_t = sleep_t[0]
            delta_minutes = int((action.TimeStamp - sleep_t).total_seconds()/60)
            action.Detail = "从{0}到{1}，睡了{2}小时{3}分钟".format(sleep_t.strftime( "%H:%M"), \
                action.TimeStamp.strftime( "%H:%M"), int(delta_minutes/60), delta_minutes%60)
    
    
    ImageFileTemplate = config.ImageRoot + r"{0}_{1}.jpg"
    def process_img_post(self, msg):
        timag_name = "D:\\tmp\\{0}_{1}.jpg".format(msg.TimeStamp.strftime("%Y_%m_%d_%H_%M"), msg.MediaId[:6])
        img_name = self.ImageFileTemplate.format(msg.TimeStamp.strftime("%Y_%m_%d_%H_%M"), msg.MediaId[:6])
        urllib.request.urlretrieve(msg.PicUrl, timag_name)
        cn_utility.reshapimg(timag_name, img_name)
        return "收到照片"

    def GenResponse(self, action):
        response = "抱歉没听懂."
        
        if action.Type == ActionType.Feed:
            response = "收到,萝卜在{1}吃了{0}".format(action.Detail, action.TimeStamp.strftime( "%H:%M"))
        elif action.Type == ActionType.Reports:
            response = "统计结果:"
            cur = datetime.datetime.utcnow() + datetime.timedelta(days=2)
            actions = self.rlSQL.GetActionReports(30)
            actions.sort(key=lambda a:a.TimeStamp)
            for a in actions:
                if a.Status == Action.Deleted:
                    continue

                if a.Type not in self.actiontype_skip_log :
                    if a.TimeStamp.day != cur.day:
                        cur = a.TimeStamp
                        response += "\n{0}日记录:\n".format(cur.strftime("%m-%d"))
                    response += (a.GenBrief() + "\n")
        elif action.Type == ActionType.WeeklyReports:
            response = "统计结果: \n"
            cur = datetime.datetime.utcnow() + datetime.timedelta(days=2)
            actions = self.rlSQL.GetActionReports(300)
            milk = 0
            breast = 0
            breastNum = 0
            poop = 0
            sleep = 0
            daysShown = 0
            for a in actions:
                if a.Status == Action.Deleted:
                    continue

                if a.TimeStamp.day != cur.day and (milk !=0 or breast !=0):                        
                    response += "{0}日：奶瓶{1}mL，母乳{2}次共{3}分钟，睡觉{5}小时{6}分钟，大便{4}次\n".format(\
                    cur.strftime("%m-%d"), milk, breastNum, breast, poop, int(sleep/60), sleep%60)
                    milk = 0
                    breast = 0 
                    poop = 0
                    breastNum = 0
                    sleep = 0
                    daysShown += 1
                    if daysShown >= 8 : break
                cur = a.TimeStamp
                if a.Type == ActionType.Feed:
                    nums = re.findall(r"\d+",a.Detail)
                    if len(nums) > 0:
                        d = int(nums[0])
                        if a.Detail.find("母乳") >= 0:
                            breast += d
                            breastNum += 1
                        elif a.Detail.find("奶瓶") >= 0:
                            milk += d
                elif a.Type == ActionType.Poop:
                    poop += 1
                elif a.Type == ActionType.WakeUp:
                    ect = extract_cn_time()
                    sleep += ect.extract_time_delta(a.Detail)
                elif a.Type == ActionType.Notes:
                    #response += "{0}日{1}\n".format(cur.strftime("%m-%d"),a.GenBrief())
                    pass

            if (milk !=0 or breast !=0) and daysShown < 7:                 
                response += "{0}日：奶瓶{1}mL，母乳{2}次共{3}分钟，睡觉{5}小时{6}分钟，大便{4}次\n".format(\
                    cur.strftime("%m-%d"), milk, breastNum, breast, poop, int(sleep/60), sleep%60)
                    
        elif action.Type == ActionType.Remove:
            self.rlSQL.DeleteLastAction()
            response ="已删除一条记录.\n"
        elif action.Type == ActionType.ListImage:
            return action.ImageList
        elif action.Type == ActionType.DebugMsg:
            msg_list = self.rlSQL.GetLastNumMsg()
            response = "List:\n"
            for m in msg_list:
                response +="T:{0}, U:{1}, M:{2} \n".format("", self.user_mapping.get(m.FromUser, default=m.FromUser), m.RawContent)
        elif action.Type == ActionType.NoPermission:
            response = "抱歉您没有权限，可以尝试 '总结' 或 '一周总结' 查看萝卜成长状态。"
        else:
            response = action.GenBrief()

        return response 

    def Receive(self, raw_str):
        msg = Message(raw_str)
        self.rlSQL.LogMessage(msg)

        if msg.MsgType == "image":
            return self.process_img_post(msg)
        
        action = self.DetectAction(msg)
        if action.Type not in self.actiontype_skip_log :
            self.rlSQL.AppendAction(action)
        else:
            pass
        
        return self.GenResponse(action)
    


