import dbWrapper
import entityClasses
import cn_utility

def GetWarnings(rlSQL):
    ret = ""
    if NeedAD(rlSQL):
        ret += "\n该考虑吃AD了。"
    return ret

def NeedAD(rlSQL):
    ad_action = rlSQL.GetLastAD()
    n = cn_utility.GetNowForUTC8()
    hour_delta = (n - ad_action.TimeStamp).seconds / 60
    return hour_delta > 12
