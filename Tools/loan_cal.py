import math

def loan_cal(y_input, ir_input):
    y = y_input #贷款年份
    ir = ir_input/100 #年化投资回报

    r = 5.2/100 #年利率
    mr = r/12    #月利率
    m = y*12      #贷款总月数
    p = 280*10000  #贷款本金
    
    mir = pow( (1+ir),1/12) -1 #月投资回报

    print('\r\n贷款年份：{}，投资利息：{}，每月利息：{}'.format(y, round(ir*100,2), round(mir*100,2)))

    mp1 = (p*mr*math.pow(1+mr, m))/(math.pow(1+mr, m)-1)  #等额本息月供，每月月供相等

    total = 0
    delta_total = 0
    invest_total= p #假设不提前还款，投资金额
    year_r = [0 for i in range(y)]

    for i in range(0, m):
        m_r = (p - i*p/m) * mr #当月利息
        year = int(i/12) #第几年
        year_r[year] += m_r #第n年利息累加
        
        mp2 = (p / m) + m_r  #等额本金月供，每月月供不相等
        total += mp2 
        #print('等额本金第{}个月:月供：{}元,利息：{}元，年累计：{}'.format(i+1, round(mp2, 2), round(m_r,2), round(year_r[year])))

        #invest_total -= mp2 #投资金额每月减少，提前留出月供
        m_i = invest_total * mir #当月投资回报
        invest_total += m_i #总投资池
        invest_total -= mp2 #投资金额每月减少，精细化运营，最后一天提取月供
        #print('等额本金第{}月：投资回报{}元，总资金池{}'.format( i+1, round(m_i, 2), round(invest_total, 2)))
        #print('投资-利息{}'.format(m_i-m_r))

        delta_m = mp1 - mp2
        delta_total += (delta_m/(pow(1+mr,i)))
        #print('等息-等金：当月{}，累计{}'.format(round(delta_m,2), round(delta_total,2)))


    print('等额本金共还款：{}元,其中利息：{}元。'.format(round(total, 2), round(total-p,2)))
    print('月周期滚动,投资回报{}'.format( round(invest_total, 2)))
    print('等额本息共还款:{}元, 月供:{}元'.format(round(mp1*m, 2),round(mp1, 2)))
    print('等息-等金：累计{}'.format(round(delta_total,2)))

    invest_total=p
    for i in range(0, y):
        invest_total -= (p/y + year_r[i]) #去除当年本金及利息，提前留出月供
        m_i = invest_total * ir #当年投资回报
        invest_total += m_i #当年投资池
        #print('等额本金第{}年：投资回报{}元，总资金池{}'.format( i, round(m_i, 2), round(invest_total, 2)))
    print('年周期滚动，投资回报{}'.format( round(invest_total, 2)))

    

loan_cal(10, 5.33)
#loan_cal(20, 5.33)

#loan_cal(10, 6.33)
#loan_cal(15, 5.2)
#loan_cal(15, 5.8)

#loan_cal(5, 6)


#delta 利息 = - mr*p/m
#delta 投资回报 = mir*(last_invest_return - p/m - last_利息)
#mir must > mr; so if invest_return < 利息 then 投资回报加速下滑
#also last(invest_return - 利息) << p/m so most likely 投资回报加速下滑 so the investment earns money at the early phase
