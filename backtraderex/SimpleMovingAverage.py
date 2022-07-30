
import backtrader as bt
from pytest import param
import numpy as np #
import math

class SimpleMovingAverage(bt.Indicator):
    
    lines = ('sma')
    params  = (('period', 20),)
    
    
    def __init__(self):
        pass
    
    def next(self):
        datasum = math.sumf(self.data.get(size=self.p.period))
        self.lines.sma[0] = datasum / self.p.period #
        