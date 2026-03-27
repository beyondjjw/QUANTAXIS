"""
QUANTAXIS 情绪因子
资金流向、成交量情绪等指标因子
"""
import pandas as pd
import numpy as np
from typing import Optional
from QUANTAXIS.QAFactor.factors.register import register_factor
from QUANTAXIS.QAFactor.factors.base import QAMultiFactor_DailyBase, QATechnicalFactorBase


@register_factor("MFI", "MFI 资金流量指标")
class MFI_Factor(QATechnicalFactorBase):
    """资金流量因子"""
    
    def __init__(self, client=None, period: int = 14):
        super().__init__(f"MFI_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 MFI 因子"""
        if data is None or not all(k in data.columns for k in ['high', 'low', 'close', 'volume']):
            return pd.DataFrame()
        
        tp = (data['high'] + data['low'] + data['close']) / 3
        mf = tp * data['volume']
        
        # 正向资金流
        mf_diff = mf.diff()
        positive_mf = mf_diff.where(mf_diff > 0, 0)
        negative_mf = (-mf_diff).where(mf_diff < 0, 0)
        
        positive_sum = positive_mf.rolling(window=self.period).sum()
        negative_sum = negative_mf.rolling(window=self.period).sum()
        
        mfr = positive_sum / negative_sum
        mfi = 100 - (100 / (1 + mfr))
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            f'MFI_{self.period}': mfi.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'MFI_{self.period}']


@register_factor("VR", "VR 情绪因子")
class VR_Factor(QATechnicalFactorBase):
    """成交量情绪因子"""
    
    def __init__(self, client=None, period: int = 26):
        super().__init__(f"VR_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 VR 因子"""
        if data is None or not all(k in data.columns for k in ['close', 'volume']):
            return pd.DataFrame()
        
        close = data['close']
        volume = data['volume']
        
        # 上涨日和下跌日成交量
        change = close.diff()
        up_vol = volume.where(change > 0, 0)
        down_vol = volume.where(change < 0, 0)
        mid_vol = volume.where(change == 0, 0)
        
        up_sum = up_vol.rolling(window=self.period).sum()
        down_sum = down_vol.rolling(window=self.period).sum()
        mid_sum = mid_vol.rolling(window=self.period).sum()
        
        vr = (up_sum + mid_sum / 2) / (down_sum + mid_sum / 2) * 100
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            f'VR_{self.period}': vr.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'VR_{self.period}']


@register_factor("CMF", "CMF  Chaikin资金流")
class CMF_Factor(QATechnicalFactorBase):
    """Chaikin 资金流因子"""
    
    def __init__(self, client=None, period: int = 20):
        super().__init__(f"CMF_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 CMF 因子"""
        if data is None or not all(k in data.columns for k in ['high', 'low', 'close', 'volume']):
            return pd.DataFrame()
        
        # 资金流
        money_flow = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low']) * data['volume']
        money_flow = money_flow.fillna(0)
        
        # 累加
        cmf = money_flow.rolling(window=self.period).sum() / volume.rolling(window=self.period).sum()
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            f'CMF_{self.period}': cmf.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'CMF_{self.period}']


@register_factor("OBV", "OBV 能量潮")
class OBV_Factor(QATechnicalFactorBase):
    """能量潮因子"""
    
    def __init__(self, client=None):
        super().__init__("OBV", client)
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 OBV 因子"""
        if data is None or not all(k in data.columns for k in ['close', 'volume']):
            return pd.DataFrame()
        
        close = data['close']
        volume = data['volume']
        
        # OBV 计算
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            'OBV': obv.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return ['OBV']


@register_factor("ATR", "ATR 平均真实波幅")
class ATR_Factor(QATechnicalFactorBase):
    """平均真实波幅因子"""
    
    def __init__(self, client=None, period: int = 14):
        super().__init__(f"ATR_{period}", client)
        self.period = period
    
    def calc(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算 ATR 因子"""
        if data is None or not all(k in data.columns for k in ['high', 'low', 'close']):
            return pd.DataFrame()
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 计算真实波幅
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.period).mean()
        
        result = pd.DataFrame({
            'date': data.get('date', pd.Series(range(len(data)))),
            'code': data.get('code', 'UNKNOWN'),
            f'ATR_{self.period}': atr.values
        })
        
        return result.dropna()
    
    def get_multi_fields(self):
        return [f'ATR_{self.period}']


# 批量计算情绪因子
def calculate_all_sentiment_factors(data: pd.DataFrame) -> pd.DataFrame:
    """计算所有情绪因子并合并"""
    result_frames = []
    
    factors = [
        MFI_Factor(period=14),
        VR_Factor(period=26),
        CMF_Factor(period=20),
        OBV_Factor(),
        ATR_Factor(period=14)
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
    
    # 合并
    result = result_frames[0]
    for df in result_frames[1:]:
        common_cols = list(set(result.columns) & set(df.columns))
        if common_cols:
            result = result.merge(df, on=common_cols, how='outer')
        else:
            result = pd.concat([result, df], axis=1)
    
    return result