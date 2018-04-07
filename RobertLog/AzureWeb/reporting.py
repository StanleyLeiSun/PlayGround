#coding: utf-8
from entityClasses import Message, Action, ActionType, DailyReport
from dbWrapper import RobertLogMSSQL
from cn_utility import num_cn2digital, extract_cn_time
import re
import datetime
import config
import urllib
import config
import cn_utility
import matplotlib.pyplot as plt
import matplotlib

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams['axes.unicode_minus'] = False

def chart_for_last_days(num_days):
    data = get_dailyreport(num_days)
    #plt.axis([0, 10, 0, 100])

    milk = []
    sleep = []
    poop = []
    x = []
    index = 1
    for d in data:
        x.append(d.date.strftime("%m.%d"))
        index += 1
        milk.append(d.milk_min*4 + d.milk_ml)
        sleep.append(d.sleep)
        poop.append(d.poop*100)
    
    #myfont = matplotlib.font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
    myfont = matplotlib.font_manager.FontProperties(fname='./wheelhouse/msyh.ttc')
    plt.plot(x,milk,label="喂奶ml",color="dodgerblue",linewidth=2)
    plt.plot(x,sleep,label="睡觉min",color="darkviolet",linewidth=2)
    plt.plot(x,poop,label=u"拉屎",color="blue",marker="o", linestyle="None")
    plt.xlabel('日期',fontproperties=myfont)
    plt.title("萝卜的日常",fontproperties=myfont)
    plt.ylim(0,1000)
    plt.grid(True)
    plt.legend(prop=myfont,loc='lower right') # bty = "n", 
    plt.show()

def get_dailyreport(num_days):

    reports = []
    rlSQL = RobertLogMSSQL(host=config.db_server,user=config.db_user,pwd=config.db_pwd,db="robertlog")

    cur = datetime.datetime.utcnow() + datetime.timedelta(days=2)
    actions = rlSQL.GetActionReports(20*num_days)
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
            reports.append(DailyReport(milk_ml = milk, milk_min = breast,\
             milk_num = breastNum, poop = poop, sleep = sleep, date = a.TimeStamp))                    
            milk = 0
            breast = 0 
            poop = 0
            breastNum = 0
            sleep = 0
            daysShown += 1
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
    return reports