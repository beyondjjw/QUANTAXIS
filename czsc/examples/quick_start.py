# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/4/27 21:51
describe: 以 Tushare 数据为例编写快速入门样例
"""
import os
import pandas as pd
from collections import OrderedDict
from czsc import CZSC, CzscAdvancedTrader, Freq
from czsc.utils import BarGenerator
from czsc import signals
from czsc.traders.ts_backtest import TsDataCache

from czsc.data.mongodata import MongoData

os.environ['czsc_verbose'] = "1"        # 是否输出详细执行信息，0 不输出，1 输出
os.environ['czsc_min_bi_len'] = "6"     # 通过环境变量设定最小笔长度，6 对应新笔定义，7 对应老笔定义
pd.set_option('mode.chained_assignment', None)
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 20)

dc = MongoData(start='2000-01-01', end='2022-02-18')


f1 = dc.get_kline_by_one_minute(code='000001', start='2015-01-01', end="2022-04-27")
c1 = CZSC(f1)
f5 = dc.get_kline_by_5minutes(code='000001', start='2015-01-01', end="2022-04-27")
c5 = CZSC(f5)
f30 = dc.get_kline_by_30minutes(code='000001', start='2015-01-01', end="2022-04-27")
c30 = CZSC(f30)

# 在浏览器中查看单标的单级别的分型、笔识别结果
bars = dc.get_kline_by_day(code='000001', start='2015-01-01', end="2022-04-27")
c = CZSC(bars)
c1.open_in_browser()

# K线合成器，这是多级别联立分析的数据支撑。示例为从日线逐K合成周线、月线
bg = BarGenerator(base_freq='1分钟', freqs=['5分钟', '30分钟', '日线', '周线'], max_count=50000)
for bar in f1:
    bg.update(bar)

# K线逐K合成结束后，通过 bg.bars 可以获取各周期K线
print("K线合成器中存下来的K线周期列表：", list(bg.bars.keys()))

# 通过K线合成器获取周线
bars_w = bg.bars['日线']


# 定义一些需要观察的信号，可以是多级别同时计算
def get_simple_signals(cat: CzscAdvancedTrader) -> OrderedDict:
    s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
    for _, c in cat.kas.items():
        if c.freq == Freq.D:
            s.update(signals.bxt.get_s_three_bi(c, di=1))
            s.update(signals.bxt.get_s_base_xt(c, di=1))

        if c.freq == Freq.W:
            s.update(signals.ta.get_s_macd(c, di=1))
            s.update(signals.ta.get_s_sma(c, di=1, t_seq=(5, 20, 60)))
    return s


def simple_strategy(symbol):
    return {"symbol": symbol, "get_signals": get_simple_signals}


cat = CzscAdvancedTrader(bg, simple_strategy)
cat.open_in_browser()

