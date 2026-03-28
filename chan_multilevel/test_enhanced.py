# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略 - 优化版
增强因子策略和技术指标
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/ws/plan/chan_multilevel')

from chan_multilevel_strategy import MultiLevelChanAnalyzer, ChanMultiLevelStrategy


def create_enhanced_data(n=100, start_price=100, trend='up'):
    """创建增强数据（含技术指标）"""
    dates = pd.date_range('2024-01-01', periods=n)
    np.random.seed(42)
    
    if trend == 'up':
        t = np.linspace(0, 20, n)
        noise = np.random.randn(n) * 2
        prices = start_price + t + noise
    elif trend == 'down':
        t = np.linspace(0, -20, n)
        noise = np.random.randn(n) * 2
        prices = start_price + t + noise
    else:  # sideway
        t = np.linspace(0, 4 * np.pi, n)
        prices = start_price + np.sin(t) * 10 + np.random.randn(n) * 2
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices - np.random.rand(n) * 0.5,
        'high': prices + np.random.rand(n) * 0.5,
        'low': prices - np.random.rand(n) * 0.5,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n),
    })
    
    # ===== 增强技术指标 =====
    # MACD
    data['ema12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['ema26'] = data['close'].ewm(span=26, adjust=False).mean()
    data['macd'] = data['ema12'] - data['ema26']
    data['signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    data['macd_hist'] = data['macd'] - data['signal']
    
    # RSI
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    #布林带
    data['bb_mid'] = data['close'].rolling(20).mean()
    data['bb_std'] = data['close'].rolling(20).std()
    data['bb_upper'] = data['bb_mid'] + 2 * data['bb_std']
    data['bb_lower'] = data['bb_mid'] - 2 * data['bb_std']
    
    # 成交量均线
    data['vol_ma5'] = data['volume'].rolling(5).mean()
    data['vol_ma20'] = data['volume'].rolling(20).mean()
    
    # 价格位置
    data['price_position'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
    
    return data


class EnhancedFactorStrategy:
    """
    增强因子策略
    综合多维度信号
    """
    
    def __init__(self):
        self.position = 0
        self.entry_price = 0
    
    def calc_trend_score(self, data: pd.DataFrame) -> float:
        """趋势因子得分"""
        score = 0.5
        
        if len(data) < 20:
            return score
        
        # 均线多头排列
        ma5 = data['close'].rolling(5).mean()
        ma10 = data['close'].rolling(10).mean()
        ma20 = data['close'].rolling(20).mean()
        
        if ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]:
            score += 0.3
        elif ma5.iloc[-1] < ma10.iloc[-1] < ma20.iloc[-1]:
            score -= 0.3
        
        # 趋势强度
        if len(data) >= 10:
            recent = data['close'].iloc[-10:].pct_change().sum()
            if recent > 0.08:
                score += 0.2
            elif recent > 0.03:
                score += 0.1
            elif recent < -0.08:
                score -= 0.2
            elif recent < -0.03:
                score -= 0.1
        
        # 收盘价位置
        if len(data) >= 20:
            high20 = data['high'].rolling(20).max().iloc[-1]
            low20 = data['low'].rolling(20).min().iloc[-1]
            close = data['close'].iloc[-1]
            pos = (close - low20) / (high20 - low20) if high20 > low20 else 0.5
            if pos > 0.8:
                score += 0.1
            elif pos < 0.2:
                score -= 0.1
        
        return max(0, min(1, score))
    
    def calc_momentum_score(self, data: pd.DataFrame) -> float:
        """动量因子得分"""
        score = 0.5
        
        if len(data) < 20:
            return score
        
        # MACD金叉/死叉 - 更宽松的判断
        if 'macd' in data.columns and 'signal' in data.columns:
            macd = data['macd'].iloc[-1]
            signal = data['signal'].iloc[-1]
            macd_prev = data['macd'].iloc[-2]
            signal_prev = data['signal'].iloc[-2]
            
            # 金叉：macd在signal上方且差值扩大
            if macd > signal and macd_prev <= signal_prev:
                score += 0.25
            # 死叉：macd在signal下方且差值扩大
            elif macd < signal and macd_prev >= signal_prev:
                score -= 0.25
            # macd在0轴上方
            elif macd > 0:
                score += 0.1
            # macd在0轴下方
            elif macd < 0:
                score -= 0.1
        
        # RSI
        if 'rsi' in data.columns:
            rsi = data['rsi'].iloc[-1]
            if rsi < 30:
                score += 0.2  # 超卖
            elif rsi > 70:
                score -= 0.2  # 超买
            elif 40 < rsi < 60:
                score += 0.05  # 中性偏多
        
        # MACD柱状体
        if 'macd_hist' in data.columns:
            if data['macd_hist'].iloc[-1] > 0:
                score += 0.1
        
        return max(0, min(1, score))
    
    def calc_volume_score(self, data: pd.DataFrame) -> float:
        """成交量因子得分"""
        score = 0.5
        
        if 'vol_ma5' in data.columns and 'vol_ma20' in data.columns:
            vol_ratio = data['vol_ma5'].iloc[-1] / data['vol_ma20'].iloc[-1]
            
            if vol_ratio > 1.5:
                score += 0.25  # 放量
            elif vol_ratio < 0.8:
                score -= 0.15  # 缩量
        
        return max(0, min(1, score))
    
    def calc_bollinger_score(self, data: pd.DataFrame) -> float:
        """布林带因子得分"""
        score = 0.5
        
        if 'price_position' in data.columns:
            pos = data['price_position'].iloc[-1]
            
            if pos < 0.2:
                score += 0.25  # 触及下轨，超卖
            elif pos > 0.8:
                score -= 0.15  # 触及上轨，超买
        
        return max(0, min(1, score))
    
    def generate_signal(self, data: pd.DataFrame, analyzer: MultiLevelChanAnalyzer) -> dict:
        """生成增强信号"""
        
        # 计算各维度得分
        trend_score = self.calc_trend_score(data)
        momentum_score = self.calc_momentum_score(data)
        volume_score = self.calc_volume_score(data)
        bollinger_score = self.calc_bollinger_score(data)
        
        # 综合得分 - 上涨趋势应得更高分
        total_score = (trend_score * 0.35 + 
                      momentum_score * 0.25 + 
                      volume_score * 0.2 + 
                      bollinger_score * 0.2)
        
        # 获取缠论信号
        strategy = ChanMultiLevelStrategy()
        chan_signal = strategy.analyze(analyzer)
        
        # 融合逻辑 - 因子为主，缠论辅助
        action = 'hold'
        reason = ''
        
        # 综合得分 >= 0.55 → buy
        if total_score >= 0.55:
            action = 'buy'
            reason = f"因子得分{total_score:.2f} 看多"
        # 综合得分 <= 0.45 → sell
        elif total_score <= 0.45:
            action = 'sell'
            reason = f"因子得分{total_score:.2f} 看空"
        # 缠论信号强化
        elif chan_signal['action'] == 'buy' and total_score >= 0.5:
            action = 'buy'
            reason = f"因子+缠论看多 {total_score:.2f}"
        elif chan_signal['action'] == 'sell' and total_score <= 0.5:
            action = 'sell'
            reason = f"因子+缠论看空 {total_score:.2f}"
        else:
            action = 'hold'
            reason = f"中性信号 {total_score:.2f}"
        
        return {
            'action': action,
            'score': total_score,
            'trend_score': trend_score,
            'momentum_score': momentum_score,
            'volume_score': volume_score,
            'bollinger_score': bollinger_score,
            'chan_action': chan_signal['action'],
            'reason': reason
        }


def test_enhanced():
    """测试增强策略"""
    print("="*60)
    print("增强因子策略测试")
    print("="*60)
    
    strategy = EnhancedFactorStrategy()
    
    # 测试上涨趋势
    print("\n【上涨趋势】")
    data = create_enhanced_data(100, 100, 'up')
    analyzer = MultiLevelChanAnalyzer('000001', ['日线'])
    analyzer.update('日线', data)
    signal = strategy.generate_signal(data, analyzer)
    print(f"信号: {signal['action']}")
    print(f"综合得分: {signal['score']:.3f}")
    print(f"  趋势:{signal['trend_score']:.2f} 动量:{signal['momentum_score']:.2f} "
          f"成交量:{signal['volume_score']:.2f} 布林:{signal['bollinger_score']:.2f}")
    print(f"缠论信号: {signal['chan_action']}")
    print(f"原因: {signal['reason']}")
    
    # 测试下跌趋势
    print("\n【下跌趋势】")
    data = create_enhanced_data(100, 100, 'down')
    analyzer = MultiLevelChanAnalyzer('000001', ['日线'])
    analyzer.update('日线', data)
    signal = strategy.generate_signal(data, analyzer)
    print(f"信号: {signal['action']}")
    print(f"综合得分: {signal['score']:.3f}")
    print(f"原因: {signal['reason']}")
    
    # 测试震荡
    print("\n【震荡盘整】")
    data = create_enhanced_data(100, 100, 'sideway')
    analyzer = MultiLevelChanAnalyzer('000001', ['日线'])
    analyzer.update('日线', data)
    signal = strategy.generate_signal(data, analyzer)
    print(f"信号: {signal['action']}")
    print(f"综合得分: {signal['score']:.3f}")
    print(f"原因: {signal['reason']}")
    
    # 综合对比
    print("\n" + "="*60)
    print("总结对比")
    print("="*60)
    
    results = []
    for trend in ['up', 'down', 'sideway']:
        data = create_enhanced_data(100, 100, trend)
        analyzer = MultiLevelChanAnalyzer('000001', ['日线'])
        analyzer.update('日线', data)
        signal = strategy.generate_signal(data, analyzer)
        results.append((trend, signal['action'], signal['score']))
    
    for trend, action, score in results:
        print(f"{trend:10} → {action:5} (得分: {score:.2f})")
    
    print("\n✅ 增强策略测试完成!")


if __name__ == '__main__':
    test_enhanced()