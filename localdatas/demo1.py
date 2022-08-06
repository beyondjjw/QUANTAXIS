from operator import le
import backtrader as bt
import os
from pathlib import Path
import datetime
import pandas as pd

import QUANTAXIS as QA
from QUANTAXIS.QAFetch.Fetcher import QA_quotation_adv
from QUANTAXIS.QAUtil.QAParameter import (DATABASE_TABLE, DATASOURCE,
                                          FREQUENCE, MARKET_TYPE,
                                          OUTPUT_FORMAT)

from MongoHLOC import MongoHLOC as mongodata
from localdatas.DualThrustStrategy import DualTrustStrategy as  dtStrategy 

            
BTVERSION = tuple(int(x) for x in bt.__version__.split('.'))

class FixedPerc(bt.Sizer):
    '''This sizer simply returns a fixed size for any operation

    Params:
      - ``perc`` (default: ``0.20``) Perc of cash to allocate for operation
    '''

    params = (
        ('perc', 0.20),  # perc of cash to use for operation
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        cashtouse = self.p.perc * cash
        if BTVERSION > (1, 7, 1, 93):
            size = comminfo.getsize(data.close[0], cashtouse)
        else:
            size = cashtouse // data.close[0]
        return size


       
if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(50000)
    cerebro.broker.setcommission(0.0005)

    code = '000629'
    start = '2022-04-01'
    end = '2022-07-01'

    try:
        mongo_min = mongodata().get_data_by_day(code, start, end)
    except Exception as e:
        print(str(e))
        exit()

    min_bar = bt.feeds.PandasData(dataname=mongo_min,
                                  name=code,
                                  fromdate=datetime.datetime.strptime(start, "%Y-%m-%d"),
                                  todate=datetime.datetime.strptime(end, "%Y-%m-%d"),
                                  timeframe=bt.TimeFrame.Minutes
                                  )

    cerebro.adddata(min_bar)  # 第一个被加进去的数据叫main_bar，可以用来交易
    # resample先投射数据，再adddata到cerebro
    # 分钟线加进去，可以按照交易日投射， 投射后的日线可以用来产生信号
    cerebro.resampledata(min_bar, timeframe=bt.TimeFrame.Days)

    cerebro.addstrategy(dtStrategy)
    # cerebro.optstrategy(TestStrategy,
    #                     maperiod=range(10, 31))
    cerebro.addwriter(bt.WriterFile, csv='{}.csv'.format(code))

    print('Start portfolio {}'.format(cerebro.broker.getcash()))
    cerebro.run()
    print('End portfolio {}'.format(cerebro.broker.getcash()))
    
   

    # cerebro.plot(style='candle')  #
    # cerebro.plot()
    
    