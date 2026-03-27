"""
AI 选股信号生成器
结合缠论信号和机器学习
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


class ChanSignalAI:
    """缠论 + AI 选股信号"""
    
    def __init__(self):
        self.signals = {}
        
    def analyze_kline(self, kline_data: pd.DataFrame) -> Dict:
        """
        分析K线，返回缠论信号
        
        :param kline_data: K线数据
        :return: 信号字典
        """
        if kline_data is None or len(kline_data) < 30:
            return {"status": "数据不足"}
        
        close = kline_data['close']
        
        # 简化缠论分析
        signal = {
            "status": "震荡",
            "trend": "未知",
            "bi_count": 0,  # 笔数
            "zd_count": 0,  # 中枢数
            "power": 0  # 力度
        }
        
        # 计算均线趋势
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        
        if ma5.iloc[-1] > ma20.iloc[-1]:
            signal["trend"] = "上涨"
        else:
            signal["trend"] = "下跌"
        
        # 计算力度 (收盘价变化率)
        power = (close.iloc[-1] - close.iloc[-10]) / close.iloc[-10] * 100 if len(close) >= 10 else 0
        signal["power"] = round(power, 2)
        
        # 判断状态
        if abs(power) < 2:
            signal["status"] = "震荡"
        elif power > 5:
            signal["status"] = "强势"
        elif power < -5:
            signal["status"] = "弱势"
        
        return signal
    
    def generate_buy_signals(self, kline_data: pd.DataFrame) -> List[str]:
        """
        生成买入信号
        
        :param kline_data: K线数据
        :return: 信号列表
        """
        signals = []
        analysis = self.analyze_kline(kline_data)
        
        # 条件1: 趋势上涨
        if analysis["trend"] == "上涨":
            signals.append("趋势多头")
        
        # 条件2: 强势状态
        if analysis["status"] == "强势":
            signals.append("强势突破")
        
        # 条件3: 力度足够
        if analysis["power"] > 3:
            signals.append("力度强劲")
        
        # 条件4: 底背离 (简化)
        if len(kline_data) >= 20:
            recent = kline_data['close'].tail(10)
            earlier = kline_data['close'].iloc[-20:-10]
            if recent.min() > earlier.min() and recent.max() < earlier.max():
                signals.append("底背离")
        
        return signals
    
    def generate_sell_signals(self, kline_data: pd.DataFrame) -> List[str]:
        """
        生成卖出信号
        
        :param kline_data: K线数据
        :return: 信号列表
        """
        signals = []
        analysis = self.analyze_kline(kline_data)
        
        # 条件1: 趋势下跌
        if analysis["trend"] == "下跌":
            signals.append("趋势空头")
        
        # 条件2: 弱势状态
        if analysis["status"] == "弱势":
            signals.append("弱势回调")
        
        # 条件3: 力度转负
        if analysis["power"] < -3:
            signals.append("力度衰竭")
        
        # 条件4: 顶背离 (简化)
        if len(kline_data) >= 20:
            recent = kline_data['close'].tail(10)
            earlier = kline_data['close'].iloc[-20:-10]
            if recent.max() < earlier.max() and recent.min() > earlier.min():
                signals.append("顶背离")
        
        return signals
    
    def score_stock(self, kline_data: pd.DataFrame, factors: pd.DataFrame = None) -> float:
        """
        综合评分
        
        :param kline_data: K线数据
        :param factors: 因子数据
        :return: 评分 (-100 到 100)
        """
        score = 0
        
        # 缠论信号评分
        buy_signals = self.generate_buy_signals(kline_data)
        sell_signals = self.generate_sell_signals(kline_data)
        
        score += len(buy_signals) * 10
        score -= len(sell_signals) * 10
        
        # 力度加成
        analysis = self.analyze_kline(kline_data)
        score += analysis["power"] * 2
        
        # 因子评分 (如果有)
        if factors is not None:
            if 'RSI_14' in factors.columns:
                rsi = factors['RSI_14'].iloc[-1]
                if rsi > 70:
                    score -= 10  # 超买
                elif rsi < 30:
                    score += 10  # 超卖
            
            if 'MACD' in factors.columns:
                macd = factors['MACD'].iloc[-1]
                if macd > 0:
                    score += 5
        
        return max(-100, min(100, score))


class AIStockPicker:
    """AI 股票池筛选器"""
    
    def __init__(self):
        self.chan_ai = ChanSignalAI()
        self.min_score = 30  # 最低入选分数
        
    def filter_stocks(self, 
                      stock_data: Dict[str, pd.DataFrame],
                      min_score: int = None) -> List[Dict]:
        """
        筛选股票
        
        :param stock_data: {code: kline_data}
        :param min_score: 最低分数
        :return: 符合条件的股票列表
        """
        min_score = min_score or self.min_score
        results = []
        
        for code, data in stock_data.items():
            try:
                score = self.chan_ai.score_stock(data)
                if score >= min_score:
                    buy_signals = self.chan_ai.generate_buy_signals(data)
                    sell_signals = self.chan_ai.generate_sell_signals(data)
                    
                    results.append({
                        "code": code,
                        "score": score,
                        "buy_signals": buy_signals,
                        "sell_signals": sell_signals,
                        "trend": self.chan_ai.analyze_kline(data)["trend"],
                        "power": self.chan_ai.analyze_kline(data)["power"]
                    })
            except Exception as e:
                print(f"处理 {code} 失败: {e}")
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results
    
    def get_recommendations(self, 
                           stock_data: Dict[str, pd.DataFrame], 
                           top_n: int = 10) -> List[Dict]:
        """
        获取推荐股票
        
        :param stock_data: 股票数据
        :param top_n: 推荐数量
        :return: 推荐列表
        """
        filtered = self.filter_stocks(stock_data)
        return filtered[:top_n]


# 缠论买卖点检测
class ChanTradingSignals:
    """缠论交易信号"""
    
    @staticmethod
    def detect_1_buy(kline_data: pd.DataFrame) -> bool:
        """1类买点检测 (下跌背驰后的第一笔低点)"""
        if len(kline_data) < 60:
            return False
        
        close = kline_data['close']
        
        # 简化: 最近30天低点高于前60天低点
        recent_low = close.tail(30).min()
        early_low = close.iloc[-60:-30].min()
        
        return recent_low > early_low
    
    @staticmethod
    def detect_1_sell(kline_data: pd.DataFrame) -> bool:
        """1类卖点检测"""
        if len(kline_data) < 60:
            return False
        
        close = kline_data['close']
        
        # 简化: 最近30天高点低于前60天高点
        recent_high = close.tail(30).max()
        early_high = close.iloc[-60:-30].max()
        
        return recent_high < early_high
    
    @staticmethod
    def detect_2_buy(kline_data: pd.DataFrame) -> bool:
        """2类买点检测 (突破1类买点后的回调不破)"""
        # 需要更复杂的缠论分析，这里简化处理
        return ChanTradingSignals.detect_1_buy(kline_data)
    
    @staticmethod
    def detect_2_sell(kline_data: pd.DataFrame) -> bool:
        """2类卖点检测"""
        return ChanTradingSignals.detect_1_sell(kline_data)
    
    @staticmethod
    def get_all_signals(kline_data: pd.DataFrame) -> Dict[str, bool]:
        """获取所有信号"""
        return {
            "1_buy": ChanTradingSignals.detect_1_buy(kline_data),
            "1_sell": ChanTradingSignals.detect_1_sell(kline_data),
            "2_buy": ChanTradingSignals.detect_2_buy(kline_data),
            "2_sell": ChanTradingSignals.detect_2_sell(kline_data),
        }