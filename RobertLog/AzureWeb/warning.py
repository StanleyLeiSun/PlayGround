#coding: utf-8
import dbWrapper
import entityClasses
import cn_utility
from entityClasses import Message, Action

def GetWarnings(rlSQL):
    return WarningForADorCa(rlSQL)

def WarningForADorCa(rlSQL):
 
    nact = Action()
    nact.TimeStamp = cn_utility.GetNowForUTC8()
    ad_action = rlSQL.GetLastAD()
    if ad_action is None:
        ad_action = nact
    
    ca_action = rlSQL.GetLastCa()
    if ca_action is None:
        ca_action = nact
    
    pill_action = rlSQL.GetLastPill()
    if pill_action is None:
        pill_action = nact

    n = cn_utility.GetNowForUTC8()   
    hour = n.hour

    ad_hour_delta = (n - ad_action.TimeStamp).total_seconds() / 3600
    ca_hour_delta = (n - ca_action.TimeStamp).total_seconds() / 3600
    pill_hour_delta = (n - pill_action.TimeStamp).total_seconds() / 3600

    if (ad_hour_delta <= 2) or (ca_hour_delta <= 2):
        return ""
    if (pill_hour_delta < 24) and (pill_hour_delta > 8):
        return "\n今天还吃药吗？"
    elif (ad_hour_delta > 23) or (  hour >=9 and hour < 13 and ad_hour_delta > 14 ):
        return "\n该考虑吃AD了。"
    elif (ca_hour_delta > 47) or (  hour >=14 and hour < 20 and ca_hour_delta > 36 ):
        return "\n该考虑吃钙片了。"
    elif (hour >= 20) :
        return "\n刷牙了吗？"
    
    return ""

def NeedAD(rlSQL):
    ad_action = rlSQL.GetLastAD()
    n = cn_utility.GetNowForUTC8()
    hour_delta = (n - ad_action.TimeStamp).total_seconds() / 3600
    #print(ad_action.TimeStamp, n, hour_delta)
    #print (hour_delta)
    return hour_delta > 23

def NeedCa(rlSQL):
    ad_action = rlSQL.GetLastCa()
    n = cn_utility.GetNowForUTC8()
    hour_delta = (n - ad_action.TimeStamp).total_seconds() / 3600
    #print(ad_action.TimeStamp, n, hour_delta)
    return hour_delta > 23
