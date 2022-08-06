import backtrader as bt
from pathlib import Path
import pandas as pd

import QUANTAXIS as QA
from QUANTAXIS.QAFetch.Fetcher import QA_quotation_adv
from QUANTAXIS.QAUtil.QAParameter import (DATABASE_TABLE, DATASOURCE,
                                          FREQUENCE, MARKET_TYPE,
                                          OUTPUT_FORMAT)

from MongoHLOC import MongoHLOC as mongodata
from backtraderex.DualThrustStrategy import DualTrustStrategy as  dtStrategy 


'''

MACD其实就是两条指数移动平均线——EMA(12)和EMA(26)——的背离和交叉,EMA(26)可视为MACD的零轴,但是MACD呈现的消息噪声较均线少。
MACD是一种趋势分析指针,不宜同时分析不同的市场环境。以下为三种交易信号:

差离值 ( DIF值 ) 与信号线 ( DEM值,又称MACD值 ) 相交；
差离值与零轴相交；
股价与差离值的背离。

差离值 ( DIF ) 形成“快线”,信号线 ( DEM ) 形成“慢线”。若股价持续上涨,DIF 值为正,且愈来愈大；若股价持续下跌,DIF 值为负,且负的程度愈来愈大。
“快”指更短时段的EMA,而“慢”则指较长时段的EMA,最常用的是12及26日EMA。

当差离值 ( DIF ) 从下而上穿过信号线 ( DEM ) ,为买进信号；相反若从上而下穿越,为卖出信号。买卖信号可能出现频繁,需要配合其他指针 ( 如:RSI、KD ) 一同分析。 
DIF 值与 MACD 值在0轴在线,代表市场为牛市,若两者皆在0轴线之下,代表市场为熊市。 DIF 值若向上突破 MACD 值及0 轴线,为买进信号,不过若尚未突破0轴,仍不宜买进；
DIF 值若向下跌破 MACD 值及0 轴线,为卖出信号,不过若尚未跌破0轴,仍不宜卖出。
棒形图 ( MACD bar / Oscillator,OSC ) 的作用是显示出“差离值”与“信号线”的差,同时将两条线的走势具体化,以利判断差离值和信号线交叉形成的买卖信号,
例如正在下降的棒形图代表两线的差值朝负的方向走,趋势向下；靠近零轴时,差离值和信号线将相交出现买卖信号。
棒形图会根据正负值分布在零轴 ( X轴 ) 的上下。棒形图在零轴上方时表示走势较强(牛市),反之则是走势较弱(熊市)。
差离值自底向上穿过零轴代表市场气氛利好股价,相反由上而下则代表利淡股价。差离值与信号线均在零轴上方时,被称为多头市场,反之,则被称为空头市场。
当股价创新低,但MACD并没有相应创新低 ( 牛市背离 ) ,视为利好 ( 利多 ) 消息,股价跌势或将完结。
相反,若股价创新高,但MACD并没有相应创新高 ( 熊市背离 ) ,视为利淡 ( 利空 ) 消息。
同样地,若股价与棒形图不配合,也可作类似结论。
MACD是一种中长线的研判指标。当股市强烈震荡或股价变化巨大 ( 如送配股拆细等 ) 时,可能会给出错误的信号。
所以在决定股票操作时,应该谨慎参考其他指标,以及市场状况,不能完全信任差离值的单一研判,避免造成损失。


'''

class MacdMJStrategy(bt.Strategy):
    '''
    这个是根据MACD面积计算来判断是否背驰
    '''

    params = (
        # Standard MACD Parameters
        ('SHORT', 12),
        ('LONG', 26),
        ('MID', 9),
        ('atrdist', 3.0),   # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
    )

    def notify_order(self, order):
        if order.status == order.Completed:
            pass

        if not order.alive():
            self.order = None  # indicate no order is pending

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.SHORT,
                                       period_me2=self.p.LONG,
                                       period_signal=self.p.MID)

        # Cross of macd.macd and macd.signal
        # mcross 大于0 就是金叉, mcross小于0就是死叉
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        

        # Control market trend
        # 使用SMA来判断是上涨趋势还是下跌趋势,当前sma大于前N个周期的sma就是上涨
        self.sma = bt.indicators.SMA(self.data, period=self.p.smaperiod)
        self.smadir = self.sma - self.sma(-self.p.dirperiod)
        
    def _cal_macd_mj(self):
        '''
        DIFF:EMA(CLOSE,SHORT) - EMA(CLOSE,LONG);
        DEA :EMA(DIFF,MID);
        MACD:2*(DIFF-DEA),COLORSTICK;
        AMACD:=ABS(MACD);
        红柱面积:IF(MACD>0,SUM(AMACD,BARSLAST(MACD<0)),0) NODRAW;
        绿柱面积:IF(MACD<0,SUM(AMACD,BARSLAST(MACD>0)),0) NODRAW;
        BV:=SUM(MACD,0);
        红转绿:=CROSS(MACD,0);
        绿转红:=CROSS(0,MACD);
        BC:=BARSLAST(红转绿 OR 绿转红)+1;
        最高红柱子:IF(MACD>0,HHV(MACD,BC),0)  NODRAW;
        最低绿柱子:IF(MACD<0,LLV(MACD,BC),0)  NODRAW;
        HMJ:=VAR2STR(REF(红柱面积,1),2);
        LMJ:=VAR2STR(REF(绿柱面积,1),2);
        
        super(MACD, self).__init__()
        me1 = self.p.movav(self.data, period=self.p.period_me1)
        me2 = self.p.movav(self.data, period=self.p.period_me2)
        self.lines.macd = me1 - me2
        self.lines.signal = self.p.movav(self.lines.macd,
                                         period=self.p.period_signal)
        '''
        self.DIFF = self.lines.macd           # 快线 : EMA12 - EMA26, 
        self.DEA = self.lines.signal          # 慢线 : EMA9 ,        
        self.MACD = 2 * (self.DIFF - self.DEA)
        
        if self.MACD > 0:
            self.red_hist_area = self.MACD.sum() 

    def start(self):
        self.order = None  # sentinel to avoid operrations on pending order

    def next(self):
        if self.order:
            return  # pending order execution

        if not self.position:  # not in the market
            if self.mcross[0] > 0.0 and self.smadir < 0.0:
                self.order = self.buy()
                pdist = self.atr[0] * self.p.atrdist
                self.pstop = self.data.close[0] - pdist

        else:  # in the market
            pclose = self.data.close[0]
            pstop = self.pstop

            if pclose < pstop:
                self.close()  # stop met - get out
            else:
                pdist = self.atr[0] * self.p.atrdist
                # Update only if greater than
                self.pstop = max(pstop, pclose - pdist)