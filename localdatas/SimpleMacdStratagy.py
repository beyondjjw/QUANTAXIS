# -*- coding: utf-8 -*-
"""

"""

import backtrader as bt
import argparse
import backtrader.feeds as btFeeds
import numpy as np
import yfinance as yf
import pandas as pd
import talib
from MongoHLOC import MongoHLOC as mg




class SimpleMACDStrat(bt.Strategy):

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
        # Print date and close

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('LONG EXECUTED, %.2f' % order.executed.price)

            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        self.log("Close: '{0}'".format(self.data.adj_close[0]))
        print('%f %f %f %f %f %f %f %f %f %f %f %f %f' % (self.data.Indexx[0], self.data.open[0],
                                                          self.data.high[0], self.data.low[0],
                                                          self.data.close[0], self.data.adj_close[0],
                                                          self.data.volume[0], self.data.EMA_100[0],
                                                          self.data.RSI[0], self.data.CCI[0],
                                                          self.data.MACD_macd[0], self.data.MACD_sign[0],
                                                          self.data.MACD_hist[0]))

        if self.order:
            return

        if self.data.MACD_hist[0] > 0:
            if self.position.size < 0 and self.data.MACD_hist[-1] < 0:
                self.close()
                self.log('CLOSE SHORT POSITION, %.2f' % self.dataclose[0])

            elif self.position.size == 0:
                self.order = self.buy()
                self.log('OPEN LONG POSITION, %.2f' % self.dataclose[0])


        elif self.data.MACD_hist[0] < 0:
            if self.position.size > 0 and self.data.MACD_hist[-1] > 0:
                self.order = self.close()
                self.log('CLOSE LONG POSITION, %.2f' % self.dataclose[0])

            elif self.position.size == 0:
                self.order = self.sell()
                self.log('OPEN SHORT POSITION, %.2f' % self.dataclose[0])
        print('')


class BasicIndicatorsFeeded(btFeeds.PandasData):
    lines = ('Indexx', 'adj_close', 'EMA_100', 'RSI', 'CCI', 'MACD_macd', 'MACD_sign', 'MACD_hist',)

    params = (('Indexx', 0), ('adj_close', 5), ('volume', 6),
              ('EMA_100', 7), ('RSI', 8), ('CCI', 9),
              ('MACD_macd', 10), ('MACD_sign', 11), ('MACD_hist', 12),)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    code = '000629'
    start = '2022-04-01'
    end = '2022-07-01'

    try:
        current = mg().get_data_by_30minutes(code, start, end)
        down = mg().get_data_by_5minutes(code, start, end)
    except Exception as e:
        print(str(e))
        exit()

    # # Add data feed to Cerebro
    # data1 = yf.download("AAPL", start="2021-08-09", end="2021-12-21", group_by="ticker")
    data1 = current
    data1.insert(0, 'Indexx', ' ')
    data1['Indexx'] = range(len(data1))
    data1['EMA_100'] = talib.EMA(data1['Adj Close'], 100)
    data1['RSI'] = talib.RSI(data1['Adj Close'], 14)
    data1['CCI'] = talib.CCI(data1['High'], data1['Low'], data1['Adj Close'], timeperiod=14)
    data1['MACD_macd'] = talib.MACD(data1['Adj Close'], fastperiod=12, slowperiod=26, signalperiod=9)[0]
    data1['MACD_sign'] = talib.MACD(data1['Adj Close'], fastperiod=12, slowperiod=26, signalperiod=9)[1]
    data1['MACD_hist'] = talib.MACD(data1['Adj Close'], fastperiod=12, slowperiod=26, signalperiod=9)[2]
    # data1['Long_position']
    # Run Cerebro Engine
    cerebro.broker.setcash(8000000000)
    start_portfolio_value = cerebro.broker.getvalue()
    cerebro.addstrategy(SimpleMACDStrat)

    data = BasicIndicatorsFeeded(dataname=data1)
    cerebro.adddata(data)

    cerebro.run()
    cerebro.plot()
    # print(data1)
    print('-------------------')
    # print('%f' %data)
    # print(data)
    end_portfolio_value = cerebro.broker.getvalue()
    pnl = end_portfolio_value - start_portfolio_value
    print(f'Starting Portfolio Value: {start_portfolio_value:2f}')
    print(f'Final Portfolio Value: {end_portfolio_value:2f}')
    print(f'PnL: {pnl:.2f}')