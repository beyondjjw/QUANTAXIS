"""
QUANTAXIS 财务因子
ROE、毛利率、成长率等基本面因子
"""
import pandas as pd
import numpy as np
from typing import Optional
from QUANTAXIS.QAFactor.factors.register import register_factor
from QUANTAXIS.QAFactor.factors.base import QAMultiFactor_DailyBase


@register_factor("ROE", "ROE 净资产收益率")
class ROE_Factor(QAMultiFactor_DailyBase):
    """净资产收益率因子"""
    
    def __init__(self, client=None):
        super().__init__("ROE", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 ROE 因子 (需要财务数据)"""
        if data is None or 'net_profit' not in data.columns or 'equity' not in data.columns:
            return pd.DataFrame()
        
        roe = data['net_profit'] / data['equity'] * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'ROE': roe.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['ROE']


@register_factor("ROA", "ROA 资产收益率")
class ROA_Factor(QAMultiFactor_DailyBase):
    """资产收益率因子"""
    
    def __init__(self, client=None):
        super().__init__("ROA", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 ROA 因子"""
        if data is None or 'net_profit' not in data.columns or 'assets' not in data.columns:
            return pd.DataFrame()
        
        roa = data['net_profit'] / data['assets'] * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'ROA': roa.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['ROA']


@register_factor("GrossMargin", "GrossMargin 毛利率")
class GrossMargin_Factor(QAMultiFactor_DailyBase):
    """毛利率因子"""
    
    def __init__(self, client=None):
        super().__init__("GrossMargin", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算毛利率因子"""
        if data is None or 'revenue' not in data.columns or 'cost' not in data.columns:
            return pd.DataFrame()
        
        gross_margin = (data['revenue'] - data['cost']) / data['revenue'] * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'GrossMargin': gross_margin.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['GrossMargin']


@register_factor("NetMargin", "NetMargin 净利率")
class NetMargin_Factor(QAMultiFactor_DailyBase):
    """净利率因子"""
    
    def __init__(self, client=None):
        super().__init__("NetMargin", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算净利率因子"""
        if data is None or 'net_profit' not in data.columns or 'revenue' not in data.columns:
            return pd.DataFrame()
        
        net_margin = data['net_profit'] / data['revenue'] * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'NetMargin': net_margin.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['NetMargin']


@register_factor("RevenueGrowth", "RevenueGrowth 营收增长率")
class RevenueGrowth_Factor(QAMultiFactor_DailyBase):
    """营收增长率因子"""
    
    def __init__(self, client=None, period: int = 4):
        super().__init__(f"RevenueGrowth_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算营收增长率因子"""
        if data is None or 'revenue' not in data.columns:
            return pd.DataFrame()
        
        revenue = data['revenue']
        growth = (revenue / revenue.shift(self.period) - 1) * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            f'RevenueGrowth_{self.period}Q': growth.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'RevenueGrowth_{self.period}Q']


@register_factor("ProfitGrowth", "ProfitGrowth 净利润增长率")
class ProfitGrowth_Factor(QAMultiFactor_DailyBase):
    """净利润增长率因子"""
    
    def __init__(self, client=None, period: int = 4):
        super().__init__(f"ProfitGrowth_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算净利润增长率因子"""
        if data is None or 'net_profit' not in data.columns:
            return pd.DataFrame()
        
        profit = data['net_profit']
        growth = (profit / profit.shift(self.period) - 1) * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            f'ProfitGrowth_{self.period}Q': growth.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'ProfitGrowth_{self.period}Q']


@register_factor("DebtRatio", "DebtRatio 资产负债率")
class DebtRatio_Factor(QAMultiFactor_DailyBase):
    """资产负债率因子"""
    
    def __init__(self, client=None):
        super().__init__("DebtRatio", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算资产负债率因子"""
        if data is None or 'liabilities' not in data.columns or 'assets' not in data.columns:
            return pd.DataFrame()
        
        debt_ratio = data['liabilities'] / data['assets'] * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'DebtRatio': debt_ratio.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['DebtRatio']


@register_factor("CurrentRatio", "CurrentRatio 流动比率")
class CurrentRatio_Factor(QAMultiFactor_DailyBase):
    """流动比率因子"""
    
    def __init__(self, client=None):
        super().__init__("CurrentRatio", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算流动比率因子"""
        if data is None or 'current_assets' not in data.columns or 'current_liabilities' not in data.columns:
            return pd.DataFrame()
        
        current_ratio = data['current_assets'] / data['current_liabilities']
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'CurrentRatio': current_ratio.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['CurrentRatio']


# 批量计算财务因子
def calculate_all_fundamental_factors(data: pd.DataFrame) -> pd.DataFrame:
    """计算所有财务因子并合并"""
    result_frames = []
    
    factors = [
        ROE_Factor(),
        ROA_Factor(),
        GrossMargin_Factor(),
        NetMargin_Factor(),
        RevenueGrowth_Factor(period=4),
        ProfitGrowth_Factor(period=4),
        DebtRatio_Factor(),
        CurrentRatio_Factor()
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