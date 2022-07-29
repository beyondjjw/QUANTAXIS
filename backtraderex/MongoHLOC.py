import datetime
import pandas as pd
import backtrader.feeds as btfeed
import QUANTAXIS as QA
from QUANTAXIS.QAFetch.Fetcher import QA_quotation_adv
from QUANTAXIS.QAUtil.QAParameter import (DATABASE_TABLE, DATASOURCE,
                                          FREQUENCE, MARKET_TYPE,
                                          OUTPUT_FORMAT)


class MongoHLOC():

    def __init__(self, frequence=FREQUENCE.ONE_MIN, **kwargs):
        self.freq = frequence

    def get_stock_data(self, code, start, end):
        df = QA_quotation_adv(code, start, end, frequence=self.freq,
                              market=MARKET_TYPE.STOCK_CN, source=DATASOURCE.AUTO, output=OUTPUT_FORMAT.DATAFRAME)
        df.reset_index(drop=False, inplace=True)

        if self.freq == FREQUENCE.DAY:
            df['datetime'] = pd.to_datetime(
                df['date'])  # 分钟线只有datetime, 日线只有date

        df.set_index('datetime', inplace=True)  #
        return df
