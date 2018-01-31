#coding: utf-8
#import re
#import string

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
            if val >= 10 and i == 0:  #应对 十三 十四 十*之类
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