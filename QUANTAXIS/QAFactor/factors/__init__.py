"""
QUANTAXIS 因子模块
因子注册与导出
"""
from QUANTAXIS.QAFactor.factors.base import (
    QAMultiFactor_DailyBase,
    QATechnicalFactorBase,
    register_factor,
    get_factor,
    list_factors,
    FACTOR_REGISTRY
)

# 技术因子
from QUANTAXIS.QAFactor.factors.technical import (
    MACD_Factor, RSI_Factor, KDJ_Factor, BOLL_Factor,
    CCI_Factor, WR_Factor, BIAS_Factor,
    calculate_all_technical_factors
)

# 情绪因子
from QUANTAXIS.QAFactor.factors.sentiment import (
    MFI_Factor, VR_Factor, CMF_Factor, OBV_Factor, ATR_Factor,
    calculate_all_sentiment_factors
)

# 财务因子
from QUANTAXIS.QAFactor.factors.fundamental import (
    ROE_Factor, ROA_Factor, GrossMargin_Factor, NetMargin_Factor,
    RevenueGrowth_Factor, ProfitGrowth_Factor, DebtRatio_Factor, CurrentRatio_Factor,
    calculate_all_fundamental_factors
)

# 行业因子
from QUANTAXIS.QAFactor.factors.industry import (
    IndustryMomentum_Factor, RS_Industry_Factor, IndustryTurnover_Factor,
    IndustryVolatility_Factor, StockInIndustry_Factor, LeadStock_Factor,
    calculate_all_industry_factors
)

__all__ = [
    # 基类
    'QAMultiFactor_DailyBase', 'QATechnicalFactorBase',
    'register_factor', 'get_factor', 'list_factors', 'FACTOR_REGISTRY',
    # 技术因子
    'MACD_Factor', 'RSI_Factor', 'KDJ_Factor', 'BOLL_Factor',
    'CCI_Factor', 'WR_Factor', 'BIAS_Factor', 'calculate_all_technical_factors',
    # 情绪因子
    'MFI_Factor', 'VR_Factor', 'CMF_Factor', 'OBV_Factor', 'ATR_Factor',
    'calculate_all_sentiment_factors',
    # 财务因子
    'ROE_Factor', 'ROA_Factor', 'GrossMargin_Factor', 'NetMargin_Factor',
    'RevenueGrowth_Factor', 'ProfitGrowth_Factor', 'DebtRatio_Factor', 'CurrentRatio_Factor',
    'calculate_all_fundamental_factors',
    # 行业因子
    'IndustryMomentum_Factor', 'RS_Industry_Factor', 'IndustryTurnover_Factor',
    'IndustryVolatility_Factor', 'StockInIndustry_Factor', 'LeadStock_Factor',
    'calculate_all_industry_factors',
]

# 自动注册所有因子
def _register_all_factors():
    all_factors = [
        MACD_Factor, RSI_Factor, KDJ_Factor, BOLL_Factor,
        CCI_Factor, WR_Factor, BIAS_Factor,
        MFI_Factor, VR_Factor, CMF_Factor, OBV_Factor, ATR_Factor,
        ROE_Factor, ROA_Factor, GrossMargin_Factor, NetMargin_Factor,
        RevenueGrowth_Factor, ProfitGrowth_Factor, DebtRatio_Factor, CurrentRatio_Factor,
        IndustryMomentum_Factor, RS_Industry_Factor, IndustryTurnover_Factor,
        IndustryVolatility_Factor, StockInIndustry_Factor, LeadStock_Factor,
    ]
    for factor_cls in all_factors:
        try:
            instance = factor_cls()
            FACTOR_REGISTRY[instance.factor_name] = factor_cls
        except Exception as e:
            print(f"Warning: Failed to register {factor_cls.__name__}: {e}")

_register_all_factors()