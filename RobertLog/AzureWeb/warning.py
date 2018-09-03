#coding: utf-8
import dbWrapper
import entityClasses
import cn_utility

def GetWarnings(rlSQL):
    return WarningForADorCa(rlSQL)

def WarningForADorCa(rlSQL):
    ad_action = rlSQL.GetLastAD()
    ca_action = rlSQL.GetLastCa()
    n = cn_utility.GetNowForUTC8()
    hour = n.hour

    ad_hour_delta = (n - ad_action.TimeStamp).total_seconds() / 3600
    ca_hour_delta = (n - ca_action.TimeStamp).total_seconds() / 3600

    if (ad_hour_delta <= 2) or (ca_hour_delta <= 2):
        return ""
    elif (ad_hour_delta > 23) or (  hour >=9 and hour < 13 and ad_hour_delta > 14 ):
        return "\n该考虑吃AD了。"
    elif (ca_hour_delta > 23) or (  hour >=14 and ca_hour_delta > 14 ):
        return "\n该考虑吃钙片了。"
    
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
