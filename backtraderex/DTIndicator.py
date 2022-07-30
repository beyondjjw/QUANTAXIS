
import backtrader as bt
from pytest import param
import numpy as np
import math

from sympy import Min

#                               突破上轨做多
#------------------------------------------------------------------------------
#    |
# K_u * Range
#    |
#------------------------ open ------------------------------------------------
#    |
# K_d * Range
#    |
#------------------------------------------------------------------------------ 
#                               跌破下轨做空
#


# -------------- HH                             HH：  N 日内最高价的最高价
#                |
#                |
#               HH - LC
# ---------------------------- HC               HC:   N 日内收盘价的最高价
#                |              |
# -------------- LC            HC - LL          LC:   N 日内收盘价的最低价
#                               |
# ---------------------------- LL               LL:   N 日内最低价的最低价

# 需要配合震荡类指标RSI等，过滤震荡行情。在股票及期货交易中，突破价位后，配合成交量的缩放效果更好。可用收盘价方式，过滤K线中最高价、最低价对买卖信号的影响。
# 当K_u<K_d时，多头相对容易被触发。当K_u>K_d时，空头相对容易被触发。
# 为了提高效率，加入一些简单的交易规则，如初始止损，跨周期的数据引用等进行完善。
# 具体地，初始资金100万，每次30%仓位开仓，日内突破上轨且30min周期的MA5>MA10，开多。日内跌破下轨且30分钟周期MA5<MA10，则平多。
    

class DTIndicator(bt.Indicator):
    lines = ('upperLine', 'lowerLine')
    params = (('period', 2), ('K_u', 0.7), ('K_d', 0.7))
    
    def __init__(self): #
        self.addminperiod(self.p.period + 1)
        
        
    # N日High的最高价HH, N日Close的最低价LC;
    # N日Close的最高价HC，N日Low的最低价LL;
    # Range = Max(HH-LC,HC-LL)
    #
    # Dual Thrust对于多头和空头的触发条件，考虑了非对称的幅度，
    # 做多和做空参考的Range可以选择不同的周期数，也可以通过参数 K_u 和 K_d 来确定。
    # 上轨(upperLine )= Open + K_u * Range
    # 下轨(lowerLine )= Open - K_d * Range
   
    def next(self):  
        HH = max(self.data.high.get(-1, size=self.p.period))
        HC = max(self.data.close.get(-1, size=self.p.period))
        LC = min(self.data.close.get(-1, size=self.p.period))
        LL = min(self.data.low.get(-1, size=self.p.period))
        
        Range = max(HH - LC, HC - LL)
        
        self.lines.upperLine[0] = self.data.open[0] + self.p.K_u * Range
        self.lines.lowerLine[0] = self.data.open[0] - self.p.K_d * Range 
        
        