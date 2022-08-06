import datetime
from xmlrpc.client import DateTime
import pandas as pd
import backtrader.feeds as btfeed
import os
from czsc.data.ts import *
from czsc.envs import *
from czsc.enum import *
from czsc.utils import io
import QUANTAXIS as QA
from QUANTAXIS.QAFetch.Fetcher import QA_quotation_adv
from QUANTAXIS.QAUtil.QAParameter import (DATABASE_TABLE, DATASOURCE,
                                          FREQUENCE, MARKET_TYPE,
                                          OUTPUT_FORMAT)

def format_kline(kline: pd.DataFrame, freq: Freq) -> List[RawBar]:
    """Tushare K线数据转换

    :param kline: dataframe K线数据
    :param freq: K线周期
    :return: 转换好的K线数据
    """
    bars = []
    dt_key = 'trade_date'
    records = kline.to_dict('records')

    for i, record in enumerate(records):
        if freq == Freq.D:
            vol = int(record['volume']*100)
            amount = int(record.get('amount', 0)*1000)
        else:
            vol = int(record['volume'])
            amount = int(record.get('amount', 0))

        # 将每一根K线转换成 RawBar 对象
        bar = RawBar(symbol=record['code'], dt=pd.to_datetime(record[dt_key]),
                     id=i, freq=freq, open=record['open'], close=record['close'],
                     high=record['high'], low=record['low'],
                     vol=vol,          # 成交量，单位：股
                     amount=amount,    # 成交额，单位：元
                     )
        bars.append(bar)
    return bars 
 

class MongoData():

    def __init__(self, start="20120101", end=datetime.now()):
        self.date_fmt = "%Y-%m-%d"
        self.start_dt = pd.to_datetime(start).strftime(self.date_fmt)
        self.end_dt = pd.to_datetime(end).strftime(self.date_fmt)
        self.freq_map = {
            FREQUENCE.ONE_MIN: Freq.F1,
            FREQUENCE.FIVE_MIN: Freq.F5,
            FREQUENCE.FIFTEEN_MIN: Freq.F15,
            FREQUENCE.THIRTY_MIN: Freq.F30,
            FREQUENCE.SIXTY_MIN: Freq.F60,
            FREQUENCE.DAY: Freq.D,
            FREQUENCE.WEEK: Freq.W,
            FREQUENCE.MONTH: Freq.M,
        }
        
    
    def _get_stock_data(self, code, start, end, freq=FREQUENCE.ONE_MIN):
        df = QA_quotation_adv(code, start, end, frequence=freq,
                              market=MARKET_TYPE.STOCK_CN, source=DATASOURCE.AUTO, output=OUTPUT_FORMAT.DATAFRAME)
        df.reset_index(drop=False, inplace=True)

        if freq == FREQUENCE.DAY:
            df['datetime'] = pd.to_datetime(df['date'])  # 分钟线只有datetime, 日线只有date
        df['dt'] = df['datetime']
        df['trade_date'] = df['datetime']
        
        print(df.head())
        df['avg_price'] = df['amount'] / df['volume']
        
        df.set_index('datetime', inplace=True)  #
        return df
    
    def get_kline_by_one_minute(self, code, start, end):
        freq = FREQUENCE.ONE_MIN
        df = self._get_stock_data(code, start, end, freq)
        return format_kline(df, self.freq_map[freq])
    
    def get_kline_by_5minutes(self, code, start, end):
        freq = FREQUENCE.FIVE_MIN
        df = self._get_stock_data(code, start, end, freq)
        return format_kline(df, self.freq_map[freq])
    
    def get_kline_by_30minutes(self, code, start, end):
        freq = FREQUENCE.THIRTY_MIN
        df = self._get_stock_data(code, start, end, freq)
        return format_kline(df, self.freq_map[freq])
    
    def get_kline_by_day(self, code, start, end):
        freq = FREQUENCE.DAY
        df = self._get_stock_data(code, start, end, freq)
        return format_kline(df, self.freq_map[freq])