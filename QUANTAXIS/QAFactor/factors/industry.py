"""
QUANTAXIS 行业因子
板块轮动、相对强弱等行业因子
"""
import pandas as pd
import numpy as np
from typing import Optional, List
from QUANTAXIS.QAFactor.factors.base import (
    QAMultiFactor_DailyBase,
    register_factor,
    QATechnicalFactorBase
)


@register_factor("IndustryMomentum", "IndustryMomentum 行业动量")
class IndustryMomentum_Factor(QAMultiFactor_DailyBase):
    """行业动量因子"""
    
    def __init__(self, client=None, period: int = 20):
        super().__init__(f"IndustryMomentum_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算行业动量因子"""
        if data is None or 'industry' not in data.columns or 'close' not in data.columns:
            return pd.DataFrame()
        
        # 按行业分组计算收益率
        returns = data.groupby('industry')['close'].pct_change(self.period)
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'industry': data.get('industry', 'UNKNOWN'),
            f'IndustryMomentum_{self.period}': returns.values * 100
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'IndustryMomentum_{self.period}']


@register_factor("RS_Industry", "RS_Industry 行业相对强弱")
class RS_Industry_Factor(QAMultiFactor_DailyBase):
    """行业相对强弱因子 (相对于市场的超额收益)"""
    
    def __init__(self, client=None, period: int = 20):
        super().__init__(f"RS_Industry_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算行业相对强弱因子"""
        if data is None or 'industry' not in data.columns or 'close' not in data.columns:
            return pd.DataFrame()
        
        # 个股收益率
        stock_return = data['close'].pct_change(self.period)
        
        # 行业平均收益率
        industry_return = data.groupby('industry')['close'].transform(
            lambda x: x.pct_change(self.period)
        )
        
        # 相对强弱 = 个股 - 行业
        rs = (stock_return - industry_return) * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'industry': data.get('industry', 'UNKNOWN'),
            f'RS_Industry_{self.period}': rs.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'RS_Industry_{self.period}']


@register_factor("IndustryTurnover", "IndustryTurnover 行业换手率")
class IndustryTurnover_Factor(QAMultiFactor_DailyBase):
    """行业换手率因子"""
    
    def __init__(self, client=None, period: int = 20):
        super().__init__(f"IndustryTurnover_{self.period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算行业换手率因子"""
        if data is None or 'industry' not in data.columns or 'volume' not in data.columns:
            return pd.DataFrame()
        
        # 按行业计算平均换手率
        industry_turnover = data.groupby('industry')['volume'].transform(
            lambda x: x.rolling(window=self.period).mean() / x.rolling(window=self.period).mean().shift(1)
        ) * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'industry': data.get('industry', 'UNKNOWN'),
            f'IndustryTurnover_{self.period}': industry_turnover.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'IndustryTurnover_{self.period}']


@register_factor("IndustryVolatility", "IndustryVolatility 行业波动率")
class IndustryVolatility_Factor(QAMultiFactor_DailyBase):
    """行业波动率因子"""
    
    def __init__(self, client=None, period: int = 20):
        super().__init__(f"IndustryVolatility_{self.period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算行业波动率因子"""
        if data is None or 'industry' not in data.columns or 'close' not in data.columns:
            return pd.DataFrame()
        
        # 按行业计算收益率标准差
        industry_vol = data.groupby('industry')['close'].transform(
            lambda x: x.pct_change().rolling(window=self.period).std()
        ) * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'industry': data.get('industry', 'UNKNOWN'),
            f'IndustryVolatility_{self.period}': industry_vol.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'IndustryVolatility_{self.period}']


@register_factor("StockInIndustry", "StockInIndustry 行业内排名因子")
class StockInIndustry_Factor(QAMultiFactor_DailyBase):
    """行业内排名因子 (市值/换手率排名)"""
    
    def __init__(self, client=None, metric: str = 'close'):
        super().__init__(f"StockInIndustry_{metric}", client)
        self.metric = metric  # 'close', 'volume', 'turnover'
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算行业内排名因子"""
        if data is None or 'industry' not in data.columns or self.metric not in data.columns:
            return pd.DataFrame()
        
        # 按行业计算排名百分位
        def rank_percentile(x):
            return x.rank(pct=True) * 100
        
        stock_rank = data.groupby('industry')[self.metric].transform(rank_percentile)
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'industry': data.get('industry', 'UNKNOWN'),
            f'StockInIndustry_{self.metric}': stock_rank.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'StockInIndustry_{self.metric}']


@register_factor("LeadStock", "LeadStock 行业领涨因子")
class LeadStock_Factor(QAMultiFactor_DailyBase):
    """行业领涨因子 (行业涨幅前N%的股票)"""
    
    def __init__(self, client=None, top_pct: float = 0.2):
        super().__init__(f"LeadStock_{int(top_pct*100)}", client)
        self.top_pct = top_pct
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算行业领涨因子"""
        if data is None or 'industry' not in data.columns or 'close' not in data.columns:
            return pd.DataFrame()
        
        # 计算收益率
        returns = data.groupby('industry')['close'].transform(
            lambda x: x.pct_change(20)
        )
        
        # 判断是否属于行业前20%
        def is_top(x):
            return x >= x.quantile(1 - self.top_pct)
        
        is_lead = data.groupby('industry')['close'].transform(
            lambda x: is_top(x.pct_change(20))
        ).astype(int)
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'industry': data.get('industry', 'UNKNOWN'),
            'LeadStock': is_lead.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['LeadStock']


# 批量计算行业因子
def calculate_all_industry_factors(data: pd.DataFrame) -> pd.DataFrame:
    """计算所有行业因子并合并"""
    result_frames = []
    
    factors = [
        IndustryMomentum_Factor(period=20),
        RS_Industry_Factor(period=20),
        IndustryTurnover_Factor(period=20),
        IndustryVolatility_Factor(period=20),
        StockInIndustry_Factor(metric='volume'),
        LeadStock_Factor(top_pct=0.2)
    ]
    
    for factor in factors:
        try:
            df = factor.calc(data)
            if not df.empty:
                result_frames.append(df)
        except Exception as e:
            print(f"Error calculating {factor.factor_name}: {e}")
    
    if not result_frames:
        return pd.DataFrame()
    
    result = result_frames[0]
    for df in result_frames[1:]:
        common_cols = list(set(result.columns) & set(df.columns))
        if common_cols:
            result = result.merge(df, on=common_cols, how='outer')
        else:
            result = pd.concat([result, df], axis=1)
    
    return result