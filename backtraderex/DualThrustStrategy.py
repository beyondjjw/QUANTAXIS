

from datetime import datetime
from datetime import time
import backtrader as bt

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
        
 
class DualTrustStrategy(bt.Strategy):
    
    def __init__(self):
        self.dataclose = self.data0.close # 使用分钟线来交易 self.data.close
        self.dtInd = DTIndicator(self.data1)   # 使用日线产生交易信号
        self.dtInd = self.dtInd()
        # self.dtInd.plotinfo.plot = False #
        self.dtInd.plotinfo.plotmaster = self.data0
        # self.dtInd.plotinfo.plotmaster = self.data1 
        
        self.buy_signal = bt.indicators.CrossOver(self.dataclose, self.dtInd.upperLine)
        self.sell_signal = bt.indicators.CrossDown(self.dataclose, self.dtInd.lowerLine)
        
        
    def start(self, order=None):
        # print("starting strategy")
        pass

    def prenext(self):
        # print("prenext strategy")
        pass

    def nextstart(self):
        # print("nextstart strategy")
        pass

    def next(self):
        data_timenow = self.data.datetime.time()
        # current = time(9, 30)
        if data_timenow > time(9, 30) and data_timenow < time(14, 52):
            if not self.position and self.buy_signal[0] == 1 :
                self.order = self.buy(size = 100)
            
            if self.position and self.sell_signal[0] == 1 :
                self.log(len(self.position))
                self.order = self.sell(size = 100)
                
            # if self.getposition().size < 0 and self.buy_signal[0] == 1 :
            #     self.order = self.close()
            #     self.order = self.buy(size = 2000) #
            
            if self.getposition().size > 0 and self.sell_signal[0] == 1 :
                self.order = self.sell(size = 100)

        # self.log("Close {}".format(self.data.close[0]))
        # print("next strategy, a new bar")  #


    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        print("{} {}".format(dt.isoformat(), txt))  #

    def stop(self):
        print("stop strategy")

    def notify_order(self, order):
        
        print("notify_order strategy %d"%order.status)