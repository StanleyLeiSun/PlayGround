#coding: utf-8
import re
import string

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
        number = re.compile(u"[一二三四五六七八九零十百千万亿]*")
        #number = re.compile(u"[一二三四五六七八九零十百千万亿]+|[0-9]+[,]*[0-9]+.[0-9]+")
        #number = re.compile("[1-9]")
        pattern = re.compile(number)
        all = pattern.findall(cn_str)
        for i in all:
            if len(i) > 0:
                d = self.chinese2digits(i)
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