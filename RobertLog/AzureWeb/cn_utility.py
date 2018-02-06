#coding: utf-8
import re
import string
import datetime

class num_cn2digital:

    def __init__(self):
        self.common_used_numerals_tmp = {'零':0, '一':1, '二':2, '两':2,\
        '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10,\
        '百':100, '千':1000, '万':10000, '亿':100000000}
        
        self.common_used_numerals = {}
        for key in self.common_used_numerals_tmp:
            self.common_used_numerals[key] = self.common_used_numerals_tmp[key]


    def chinese2digits(self, uchars_chinese) :
        total = 0
        r = 1 #unit 1,10,100 or ...
        for i in range(len(uchars_chinese) - 1, -1, -1):
            val = self.common_used_numerals.get(uchars_chinese[i])
            if val >= 10 and i == 0: # 11,12...
                if val > r:
                    r = val
                    total = total + val
                else:
                    r = r * val
                    #total =total + r * x
            elif val >= 10:
                if val > r:
                    r = val
                else:
                    r = r * val
            else:
                total = total + r * val
        return total

    def replace_cn_digital(self, cn_str):
        ret = cn_str
        number = re.compile(u"[一二两三四五六七八九零十百千万亿]*")
        #number = re.compile(u"[一二三四五六七八九零十百千万亿]+|[0-9]+[,]*[0-9]+.[0-9]+")
        #number = re.compile("[1-9]")
        pattern = re.compile(number)
        all = pattern.findall(cn_str)
        for i in all:
            #print(i)
            if len(i) > 0:
                d = self.chinese2digits(i)
                #print(d,i)
                ret = ret.replace(i,str(d),1)
        
        return ret

    def Test(self):
        t = u"一百八"
        print("{0} => {1}", t, self.replace_cn_digital(t))
        t = u"一百毫升"
        print("{0} => {1}", t, self.replace_cn_digital(t))
        t = u"喂了一百二十毫升"
        print("{0} => {1}", t, self.replace_cn_digital(t))
        t = u"八十八"
        print("{0} => {1}", t, self.replace_cn_digital(t))


class extract_cn_time:
    
    cn_time_pattern = re.compile(r'((([0-1]?[0-9])|2[0-3]):([0-5]?[0-9])(:([0-5]?[0-9]))?)'+\
    r'|((0?[0-9]|1[0-9]|2[0-3])点\d+分?)|((0?[0-9]|1[0-9]|2[0-3])点半?)')
    cn_date_pattern = re.compile(r'((\d{4}|\d{2})(-|/|.)\d{1,2}\3\d{1,2})|(\d{4}年\d{1,2}月'+\
    r'\d{1,2}日)|(\d{1,2}月\d{1,2}日)|(\d{1,2}日)')

    def extract_time(self, cn_str):
        dt_ret = []
        tstr_list = self.cn_time_pattern.findall(cn_str)
        #print(tstr_list)
        if len(tstr_list) <= 0: return
        for tstr in tstr_list[0]:
            if len(tstr) > 0:
                hour = 0
                minute = 0
                numbs = re.findall(r'\d*', tstr)
                #print(numbs)
                hour = int(numbs[0])
                if len(numbs) > 2 and len(numbs[2]) > 0:
                    minute = int(numbs[2])
                elif r"半" in tstr:
                    minute = 30
                
                t = datetime.datetime.utcnow()  + datetime.timedelta(hours=+8)
                if t.hour > 12 and hour < 12: 
                    hour += 12 
                
                t2 = t.replace(hour = hour, minute = minute, second = 0, microsecond = 0)
                if t2 > t : 
                    t2 = t2 + datetime.timedelta(hours = -12)
                
                #print(t)
                dt_ret.append(t2)
                break
        return  dt_ret
    
    def extract_time_v2(self, cn_str):
        dt_ret = []
        tstr_list = self.cn_time_pattern.findall(cn_str)
        if len(tstr_list) <= 0: return
        for match in tstr_list:
            for tstr in match:
                if len(tstr) > 0:
                    hour = 0
                    minute = 0
                    numbs = re.findall(r'\d*', tstr)
                    #print(numbs)
                    hour = int(numbs[0])
                    if len(numbs) > 2 and len(numbs[2]) > 0:
                        minute = int(numbs[2])
                    elif r"半" in tstr:
                        minute = 30

                    t = datetime.datetime.utcnow()  + datetime.timedelta(hours=+8)
                    t2 = t.replace(hour = hour, minute = minute, second = 0, microsecond = 0)
                    dt_ret.append(t2)
                    break
        return  dt_ret
    
    def extract_time_delta(self, cn_str):
        tlist = self.extract_time_v2(cn_str)
        if len(tlist) != 2:
            return
        print(tlist)
        if tlist[0] > tlist[1]:
            tlist[0] = tlist[0] + datetime.timedelta(days = -1)
        
        print(tlist)
        return int((tlist[1] - tlist[0]).total_seconds()/60)

    def remove_time(self, cn_str):
        tstr_list = self.cn_time_pattern.findall(cn_str)
        ret = cn_str
        if len(tstr_list) <= 0 : return
        for tstr in tstr_list[0]:
            if len(tstr) > 0:
                ret = ret.replace(tstr,"", 1)
                break
        return ret

    def Test(self):

        cn2d = num_cn2digital()
        t = u"23:20 喂奶20毫升"
        print(t)
        t1 = cn2d.replace_cn_digital(t)
        print("t1:",t1)
        print( t, self.extract_time(t1))
        print(t, self.remove_time(t1))

        cn2d = num_cn2digital()
        t = u"十二点二十分"
        print(t)
        t1 = cn2d.replace_cn_digital(t)
        print("t1:",t1)
        print( t, self.extract_time(t1))
        print(t, self.remove_time(t1))

        t = u"三点半喂奶二十毫升"
        t1 = cn2d.replace_cn_digital(t)
        print("t1:",t1)
        print( t, self.extract_time(t1))
        print(t, "removed", self.remove_time(t1))

        t = u"九点五分喂了10分钟"
        t1 = cn2d.replace_cn_digital(t)
        print("t1:",t1)
        print( t, self.extract_time(t1))
        print(t, "removed", self.remove_time(t1))

        t = u"九点喂奶十分钟"
        t1 = cn2d.replace_cn_digital(t)
        print("t1:",t1)
        print( t, self.extract_time(t1))
        print(t, "removed", self.remove_time(t1))
        
