import dbWrapper
import entityClasses
import cn_utility

def GetWarnings(rlSQL):
    ret = ""
    if NeedAD(rlSQL):
        ret += "\n该考虑吃AD了。"
    if NeedCa(rlSQL):
        ret += "\n该考虑吃钙片了。"
        
    return ret

def NeedAD(rlSQL):
    ad_action = rlSQL.GetLastAD()
    n = cn_utility.GetNowForUTC8()
    hour_delta = (n - ad_action.TimeStamp).seconds / 3600
    print(ad_action.TimeStamp, n, hour_delta)
    return hour_delta > 23

def NeedCa(rlSQL):
    ad_action = rlSQL.GetLastCa()
    n = cn_utility.GetNowForUTC8()
    hour_delta = (n - ad_action.TimeStamp).seconds / 3600
    print(ad_action.TimeStamp, n, hour_delta)
    return hour_delta > 23
