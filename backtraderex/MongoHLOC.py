import datetime
import pandas as pd
import backtrader.feeds as btfeed
import QUANTAXIS as QA
from QUANTAXIS.QAFetch.Fetcher import QA_quotation_adv
from QUANTAXIS.QAUtil.QAParameter import (DATABASE_TABLE, DATASOURCE,
                                          FREQUENCE, MARKET_TYPE,
                                          OUTPUT_FORMAT)


class MongoHLOC():

    def __init__(self, **kwargs):
        pass
    
    def _get_stock_data(self, code, start, end, freq=FREQUENCE.ONE_MIN):
        df = QA_quotation_adv(code, start, end, frequence=freq,
                              market=MARKET_TYPE.STOCK_CN, source=DATASOURCE.AUTO, output=OUTPUT_FORMAT.DATAFRAME)
        df.reset_index(drop=False, inplace=True)

        if freq == FREQUENCE.DAY:
            df['datetime'] = pd.to_datetime(df['date'])  # 分钟线只有datetime, 日线只有date

        df.set_index('datetime', inplace=True)  #
        return df
    
    def get_data_by_one_minute(self, code, start, end):
        freq = FREQUENCE.ONE_MIN
        return self._get_stock_data(code, start, end, freq)
    
    def get_data_by_5minutes(self, code, start, end):
        freq = FREQUENCE.FIVE_MIN
        return self._get_stock_data(code, start, end, freq)
    
    def get_data_by_30minutes(self, code, start, end):
        freq = FREQUENCE.THIRTY_MIN
        return self._get_stock_data(code, start, end, freq)
    
    def get_data_by_day(self, code, start, end):
        freq = FREQUENCE.DAY
        return self._get_stock_data(code, start, end, freq)