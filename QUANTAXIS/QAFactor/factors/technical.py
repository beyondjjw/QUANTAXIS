# coding:utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2021 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
技术因子模块

包含 MACD, RSI, KDJ, BOLL, CCI, WR, BIAS 等常用技术指标因子
"""

import pandas as pd

from QUANTAXIS.QAFactor.factors.base import QAMultiFactor_DailyBase
from QUANTAXIS.QAFactor.factors.register import register_factor
from QUANTAXIS.QAIndicator.indicators import (
    QA_indicator_MACD,
    QA_indicator_RSI,
    QA_indicator_KDJ,
    QA_indicator_BOLL,
    QA_indicator_CCI,
    QA_indicator_WR,
    QA_indicator_BIAS,
)


# ==================== MACD 系列因子 ====================

@register_factor("MACD_DIF", "MACD差值(DIF)", "technical")
class MACD_DIF_Factor(QAMultiFactor_DailyBase):
    """MACD DIF 因子 - 快线"""
    
    factor_column = 'DIF'
    description = 'MACD指标中的DIF线，EMA(close,12) - EMA(close,26)'
    
    def __init__(self, short: int = 12, long: int = 26, mid: int = 9, **kwargs):
        self.short = short
        self.long = long
        self.mid = mid
        super().__init__(**kwargs)
    
    def finit(self):
        """初始化数据客户端"""
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        """计算 MACD DIF"""
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        # 获取全市场数据
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL', 
            start='2015-01-01', 
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        # 计算 MACD
        macd = data.add_func(QA_indicator_MACD, self.short, self.long, self.mid)
        
        # 提取 DIF 列
        result = pd.DataFrame({
            'date': macd['date'],
            'code': macd['code'],
            'factor': macd['DIF']
        })
        return result.dropna()


@register_factor("MACD_DEA", "MACD信号线(DEA)", "technical")
class MACD_DEA_Factor(QAMultiFactor_DailyBase):
    """MACD DEA 因子 - 信号线"""
    
    factor_column = 'DEA'
    description = 'MACD指标中的DEA线，EMA(DIF,9)'
    
    def __init__(self, short: int = 12, long: int = 26, mid: int = 9, **kwargs):
        self.short = short
        self.long = long
        self.mid = mid
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        macd = data.add_func(QA_indicator_MACD, self.short, self.long, self.mid)
        
        result = pd.DataFrame({
            'date': macd['date'],
            'code': macd['code'],
            'factor': macd['DEA']
        })
        return result.dropna()


@register_factor("MACD_Hist", "MACD柱状图(MACD)", "technical")
class MACD_Hist_Factor(QAMultiFactor_DailyBase):
    """MACD Hist 因子 - 柱状图"""
    
    factor_column = 'MACD'
    description = 'MACD柱状图，(DIF-DEA)*2'
    
    def __init__(self, short: int = 12, long: int = 26, mid: int = 9, **kwargs):
        self.short = short
        self.long = long
        self.mid = mid
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        macd = data.add_func(QA_indicator_MACD, self.short, self.long, self.mid)
        
        result = pd.DataFrame({
            'date': macd['date'],
            'code': macd['code'],
            'factor': macd['MACD']
        })
        return result.dropna()


# ==================== RSI 因子 ====================

@register_factor("RSI", "相对强弱指标(RSI)", "technical")
class RSI_Factor(QAMultiFactor_DailyBase):
    """RSI 因子 - 相对强弱指标"""
    
    factor_column = 'RSI'
    description = '相对强弱指标，默认14日RSI'
    
    def __init__(self, N: int = 14, **kwargs):
        self.N = N
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        rsi = data.add_func(QA_indicator_RSI, self.N)
        
        # RSI 函数返回多列，取第一列作为主RSI
        rsi_col = rsi.columns[0]  # 通常是 'RSI'
        
        result = pd.DataFrame({
            'date': rsi['date'],
            'code': rsi['code'],
            'factor': rsi[rsi_col]
        })
        return result.dropna()


# ==================== KDJ 系列因子 ====================

@register_factor("KDJ_K", "KDJ随机指标K值", "technical")
class KDJ_K_Factor(QAMultiFactor_DailyBase):
    """KDJ K 因子"""
    
    factor_column = 'K'
    description = 'KDJ指标中的K值，默认9日参数'
    
    def __init__(self, N: int = 9, M1: int = 3, M2: int = 3, **kwargs):
        self.N = N
        self.M1 = M1
        self.M2 = M2
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        kdj = data.add_func(QA_indicator_KDJ, self.N, self.M1, self.M2)
        
        result = pd.DataFrame({
            'date': kdj['date'],
            'code': kdj['code'],
            'factor': kdj['K']
        })
        return result.dropna()


@register_factor("KDJ_D", "KDJ随机指标D值", "technical")
class KDJ_D_Factor(QAMultiFactor_DailyBase):
    """KDJ D 因子"""
    
    factor_column = 'D'
    description = 'KDJ指标中的D值'
    
    def __init__(self, N: int = 9, M1: int = 3, M2: int = 3, **kwargs):
        self.N = N
        self.M1 = M1
        self.M2 = M2
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        kdj = data.add_func(QA_indicator_KDJ, self.N, self.M1, self.M2)
        
        result = pd.DataFrame({
            'date': kdj['date'],
            'code': kdj['code'],
            'factor': kdj['D']
        })
        return result.dropna()


@register_factor("KDJ_J", "KDJ随机指标J值", "technical")
class KDJ_J_Factor(QAMultiFactor_DailyBase):
    """KDJ J 因子"""
    
    factor_column = 'J'
    description = 'KDJ指标中的J值，3*K-2*D'
    
    def __init__(self, N: int = 9, M1: int = 3, M2: int = 3, **kwargs):
        self.N = N
        self.M1 = M1
        self.M2 = M2
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        kdj = data.add_func(QA_indicator_KDJ, self.N, self.M1, self.M2)
        
        result = pd.DataFrame({
            'date': kdj['date'],
            'code': kdj['code'],
            'factor': kdj['J']
        })
        return result.dropna()


# ==================== BOLL 系列因子 ====================

@register_factor("BOLL", "布林带中轨(BOLL)", "technical")
class BOLL_Factor(QAMultiFactor_DailyBase):
    """BOLL 中轨因子 - 价格中位数"""
    
    factor_column = 'BOLL'
    description = '布林带中轨，N日收盘价均值，默认20日'
    
    def __init__(self, N: int = 20, P: int = 2, **kwargs):
        self.N = N
        self.P = P
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        boll = data.add_func(QA_indicator_BOLL, self.N, self.P)
        
        result = pd.DataFrame({
            'date': boll['date'],
            'code': boll['code'],
            'factor': boll['BOLL']
        })
        return result.dropna()


@register_factor("BOLL_UB", "布林带上轨(BOLL_UB)", "technical")
class BOLL_UB_Factor(QAMultiFactor_DailyBase):
    """BOLL 上轨因子"""
    
    factor_column = 'UB'
    description = '布林带上轨，BOLL + P*STD'
    
    def __init__(self, N: int = 20, P: int = 2, **kwargs):
        self.N = N
        self.P = P
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        boll = data.add_func(QA_indicator_BOLL, self.N, self.P)
        
        result = pd.DataFrame({
            'date': boll['date'],
            'code': boll['code'],
            'factor': boll['UB']
        })
        return result.dropna()


@register_factor("BOLL_LB", "布林带下轨(BOLL_LB)", "technical")
class BOLL_LB_Factor(QAMultiFactor_DailyBase):
    """BOLL 下轨因子"""
    
    factor_column = 'LB'
    description = '布林带下轨，BOLL - P*STD'
    
    def __init__(self, N: int = 20, P: int = 2, **kwargs):
        self.N = N
        self.P = P
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        boll = data.add_func(QA_indicator_BOLL, self.N, self.P)
        
        result = pd.DataFrame({
            'date': boll['date'],
            'code': boll['code'],
            'factor': boll['LB']
        })
        return result.dropna()


# ==================== CCI 因子 ====================

@register_factor("CCI", "商品通道指标(CCI)", "technical")
class CCI_Factor(QAMultiFactor_DailyBase):
    """CCI 因子 - 商品通道指标"""
    
    factor_column = 'CCI'
    description = '商品通道指标，默认14日'
    
    def __init__(self, N: int = 14, **kwargs):
        self.N = N
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        cci = data.add_func(QA_indicator_CCI, self.N)
        
        result = pd.DataFrame({
            'date': cci['date'],
            'code': cci['code'],
            'factor': cci['CCI']
        })
        return result.dropna()


# ==================== WR 因子 ====================

@register_factor("WR", "威廉指标(WR)", "technical")
class WR_Factor(QAMultiFactor_DailyBase):
    """WR 因子 - 威廉指标"""
    
    factor_column = 'WR'
    description = '威廉指标，默认10日'
    
    def __init__(self, N: int = 10, N1: int = 6, **kwargs):
        self.N = N
        self.N1 = N1
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        wr = data.add_func(QA_indicator_WR, self.N, self.N1)
        
        # WR 返回两列 WR 和 WR1，取第一列
        wr_col = wr.columns[0]
        
        result = pd.DataFrame({
            'date': wr['date'],
            'code': wr['code'],
            'factor': wr[wr_col]
        })
        return result.dropna()


# ==================== BIAS 因子 ====================

@register_factor("BIAS", "乖离率(BIAS)", "technical")
class BIAS_Factor(QAMultiFactor_DailyBase):
    """BIAS 因子 - 乖离率"""
    
    factor_column = 'BIAS'
    description = '乖离率，(close - MA) / MA * 100'
    
    def __init__(self, N1: int = 5, N2: int = 10, N3: int = 20, **kwargs):
        self.N1 = N1
        self.N2 = N2
        self.N3 = N3
        super().__init__(**kwargs)
    
    def finit(self):
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            self.clientr = None
    
    def calc(self) -> pd.DataFrame:
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code='ALL',
            start='2015-01-01',
            end=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        bias = data.add_func(QA_indicator_BIAS, self.N1, self.N2, self.N3)
        
        # BIAS 返回3列，取第一列作为主BIAS
        bias_col = bias.columns[0]
        
        result = pd.DataFrame({
            'date': bias['date'],
            'code': bias['code'],
            'factor': bias[bias_col]
        })
        return result.dropna()


# ==================== 技术因子批量创建函数 ====================

def create_all_technical_factors() -> dict:
    """
    创建所有技术因子实例
    
    Returns:
        {因子名: 因子实例}
    """
    factors = {
        'MACD_DIF': MACD_DIF_Factor(),
        'MACD_DEA': MACD_DEA_Factor(),
        'MACD_Hist': MACD_Hist_Factor(),
        'RSI': RSI_Factor(),
        'KDJ_K': KDJ_K_Factor(),
        'KDJ_D': KDJ_D_Factor(),
        'KDJ_J': KDJ_J_Factor(),
        'BOLL': BOLL_Factor(),
        'BOLL_UB': BOLL_UB_Factor(),
        'BOLL_LB': BOLL_LB_Factor(),
        'CCI': CCI_Factor(),
        'WR': WR_Factor(),
        'BIAS': BIAS_Factor(),
    }
    return factors


def update_all_technical_factors(start: str = '2015-01-01', end: str = None):
    """
    批量更新所有技术因子到数据库
    
    Args:
        start: 开始日期
        end: 结束日期，默认今天
    """
    if end is None:
        end = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    factors = create_all_technical_factors()
    
    for name, factor in factors.items():
        try:
            print(f"Updating {name}...")
            factor.update_to_database()
            print(f"  {name} updated successfully")
        except Exception as e:
            print(f"  Error updating {name}: {e}")