"""
AI 选股模块
集成机器学习和缠论分析
"""
from .sk import evaluate_estimator, train_estimator
from .selector import AISelector, FactorAISelector, EnsembleSelector
from .trading_signals import ChanSignalAI, AIStockPicker, ChanTradingSignals

__all__ = [
    # 模型训练
    'evaluate_estimator',
    'train_estimator',
    # 选股器
    'AISelector',
    'FactorAISelector', 
    'EnsembleSelector',
    # 缠论信号
    'ChanSignalAI',
    'AIStockPicker',
    'ChanTradingSignals',
]

# 版本信息
__version__ = "1.0.0"
__author__ = "beyondjjw"