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


def get_yahoo_csv(code='000001'):
    data_path = Path(os.getcwd()) / 'datas/000001.SZ.csv'
    date_frame = pd.read_csv(data_path)
    date_frame['datetime'] = pd.to_datetime(date_frame['Date'])  #
    date_frame.set_index('datetime', inplace=True)  #
    date_frame['openinterest'] = 0

    return date_frame


def get_mongo_data(code='000001'):
    df = QA_quotation_adv('000001', '2022-05-01', '2022-06-01', frequence=FREQUENCE.ONE_MIN,
                          market=MARKET_TYPE.STOCK_CN, source=DATASOURCE.AUTO, output=OUTPUT_FORMAT.DATAFRAME)
    df.reset_index(drop=False, inplace=True)
    # df.drop(['code'], axis=1, inplace=True)
    # df['datetime'] = pd.to_datetime(df['date'])  #分钟线只有datetime, 日线只有date
    df.set_index('datetime', inplace=True)  #
    df['openinterest'] = 0

    return df


def write_csv_to_compare_datas(first, second):
    first.to_csv('000001.first.day.csv', index=True)
    second.to_csv('000001.second.day.csv', index=True)


# 可以先写一个 dual thrust 策略测试一下
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def __init__(self):
        # 将第一个data给变量dataclose, close 是Lines对象
        self.dataclose = self.datas[0].close
        # 主数据源是分钟数据， 日线数据是投射分钟线加入到cerebro, 所以日线数据再画图的时候就不显示了
        self.data1.plotinfo.plot = False
        print("initialization")

    def start(self, order=None):
        print("starting strategy")

    def prenext(self):
        print("prenext strategy")

    def nextstart(self):
        print("nextstart strategy")

    def next(self):
        print("next strategy, a new bar")  #
        self.log("Close {}".format(self.data.close[0]))

    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        print("{} {}".format(dt.isoformat(), txt))  #

    def stop(self):
        print("stop strategy")
        print(self.params.maperiod, self.broker.getvalue())

    def notify_order(self, order):
        print("notify_order strategy")


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(50000)
    cerebro.broker.setcommission(0.0005)

    yahoo = get_yahoo_csv()
    mongo = get_mongo_data()
    write_csv_to_compare_datas(yahoo, mongo)

    min_bar = bt.feeds.PandasData(dataname=mongo,
                                  fromdate=datetime.datetime(2010, 5, 25),
                                  todate=datetime.datetime(2022, 6, 1),
                                  timeframe=bt.TimeFrame.Minutes
                                  )

    cerebro.adddata(min_bar)  # 第一个被加进去的数据叫main_bar，可以用来交易
    # resample先投射数据，再adddata到cerebro
    # 分钟线加进去，可以按照交易日投射， 投射后的日线可以用来产生信号
    cerebro.resampledata(min_bar, timeframe=bt.TimeFrame.Days)

    cerebro.addstrategy(TestStrategy)
    # cerebro.optstrategy(TestStrategy,
    #                     maperiod=range(10, 31))

    print('Start portfolio {}'.format(cerebro.broker.getcash()))
    cerebro.run()
    print('End portfolio {}'.format(cerebro.broker.getcash()))

    # cerebro.plot(style='candle')  #
    cerebro.plot()
