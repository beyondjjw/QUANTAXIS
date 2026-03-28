# -*- coding: utf-8 -*-
"""
缠论综合策略 - 多指标版本
包含: RSI/KDJ/BOLL/CCI/WR/BIAS + 缠论

作者: beyondjjw
版本: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


# ==================== 笔识别 ====================

class Bi:
    """笔结构"""
    def __init__(self, direction: str, high: float, low: float):
        self.direction = direction
        self.high = high
        self.low = low
        self.force = abs(high - low) / low if low > 0 else 0
    
    def __repr__(self):
        return f"笔({'上涨' if self.direction == 'up' else '下跌'}, 高:{self.high:.2f}, 低:{self.low:.2f})"


def identify_bi(bars: pd.DataFrame) -> List[Bi]:
    """识别笔"""
    if len(bars) < 5:
        return []
    
    bits = []
    for i in range(1, len(bars) - 1):
        curr = bars.iloc[i]
        prev = bars.iloc[i-1]
        next_ = bars.iloc[i+1]
        
        if curr['high'] >= prev['high'] and curr['high'] >= next_['high']:
            bits.append(Bi('up', curr['high'], prev['low']))
        elif curr['low'] <= prev['low'] and curr['low'] <= next_['low']:
            bits.append(Bi('down', prev['high'], curr['low']))
    
    # 合并
    merged = []
    for b in bits:
        if not merged:
            merged.append(b)
        elif b.direction == merged[-1].direction:
            merged[-1] = Bi(b.direction, 
                          max(merged[-1].high, b.high), 
                          min(merged[-1].low, b.low))
        else:
            merged.append(b)
    
    return merged


# ==================== 中枢识别 ====================

class ZhongShu:
    def __init__(self, zg: float, zd: float):
        self.zg = zg
        self.zd = zd
    
    def __repr__(self):
        return f"中枢(ZG:{self.zg:.2f}, ZD:{self.zd:.2f})"


def identify_zhongshu(bars: pd.DataFrame) -> Optional[ZhongShu]:
    """识别中枢"""
    if len(bars) < 15:
        return None
    
    highs = bars['high'].values
    lows = bars['low'].values
    
    candidates = []
    for i in range(len(bars) - 4):
        h1, h2, h3 = highs[i:i+3]
        l1, l2, l3 = lows[i:i+3]
        high = min(h1, h2, h3)
        low = max(l1, l2, l3)
        if high > low:
            candidates.append((low, high))
    
    if not candidates:
        return None
    
    candidates.sort()
    merged = []
    for c in candidates:
        if not merged or c[0] > merged[-1][1]:
            merged.append(c)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]))
    
    if not merged:
        return None
    
    return ZhongShu(merged[0][1], merged[0][0])


# ==================== 多指标计算 ====================

def calc_rsi(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算RSI"""
    delta = bars['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calc_kdj(bars: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算KDJ"""
    low_n = bars['low'].rolling(window=n).min()
    high_n = bars['high'].rolling(window=n).max()
    
    rsv = (bars['close'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)
    
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()
    d = k.ewm(alpha=1/m2, adjust=False).mean()
    j = 3 * k - 2 * d
    
    return pd.DataFrame({'k': k, 'd': d, 'j': j})


def calc_boll(bars: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """计算布林带"""
    ma = bars['close'].rolling(window=period).mean()
    std = bars['close'].rolling(window=period).std()
    
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    
    return pd.DataFrame({
        'ma': ma,
        'upper': upper,
        'lower': lower
    })


def calc_cci(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算CCI"""
    tp = (bars['high'] + bars['low'] + bars['close']) / 3
    sma = tp.rolling(window=period).mean()
    mad = (tp - sma).abs().rolling(window=period).mean()
    
    cci = (tp - sma) / (0.015 * mad)
    
    return cci


def calc_wr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算威廉指标"""
    high_n = bars['high'].rolling(window=period).max()
    low_n = bars['low'].rolling(window=period).min()
    
    wr = (high_n - bars['close']) / (high_n - low_n) * 100
    
    return wr


def calc_bias(bars: pd.DataFrame, period: int = 5) -> pd.Series:
    """计算乖离率"""
    ma = bars['close'].rolling(window=period).mean()
    bias = (bars['close'] - ma) / ma * 100
    
    return bias


def calc_all_indicators(bars: pd.DataFrame) -> Dict:
    """计算所有指标"""
    result = {}
    
    # RSI
    result['rsi'] = calc_rsi(bars).iloc[-1] if len(bars) >= 14 else 50
    
    # KDJ
    kdj = calc_kdj(bars)
    result['kdj_k'] = kdj['k'].iloc[-1] if len(bars) >= 9 else 50
    result['kdj_d'] = kdj['d'].iloc[-1] if len(bars) >= 9 else 50
    result['kdj_j'] = kdj['j'].iloc[-1] if len(bars) >= 9 else 50
    
    # BOLL
    boll = calc_boll(bars)
    close = bars['close'].iloc[-1]
    result['boll_ub'] = boll['upper'].iloc[-1] if len(bars) >= 20 else close
    result['boll_lb'] = boll['lower'].iloc[-1] if len(bars) >= 20 else close
    result['boll_pos'] = (close - boll['lower'].iloc[-1]) / (boll['upper'].iloc[-1] - boll['lower'].iloc[-1]) if len(bars) >= 20 and boll['upper'].iloc[-1] > boll['lower'].iloc[-1] else 0.5
    
    # CCI
    result['cci'] = calc_cci(bars).iloc[-1] if len(bars) >= 14 else 0
    
    # WR
    result['wr'] = calc_wr(bars).iloc[-1] if len(bars) >= 14 else 50
    
    # BIAS
    result['bias'] = calc_bias(bars).iloc[-1] if len(bars) >= 5 else 0
    
    return result


# ==================== MACD ====================

def calc_macd(bars: pd.DataFrame) -> Dict:
    """计算MACD"""
    ema12 = bars['close'].ewm(span=12).mean()
    ema26 = bars['close'].ewm(span=26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9).mean()
    macd = (dif - dea) * 2
    
    return {'dif': dif.iloc[-1], 'dea': dea.iloc[-1], 'macd': macd.iloc[-1]}


def check_macd_divergence(bars: pd.DataFrame, direction: str) -> Optional[Dict]:
    """MACD背离"""
    df = bars.copy()
    df['dif'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    
    if len(df) < 10:
        return None
    
    if direction == 'up':
        price_high = df['high'].iloc[-1]
        prev_highs = df['high'].iloc[:-1].max()
        
        if price_high > prev_highs:
            dif_high = df['dif'].iloc[-1]
            prev_difs = df['dif'].iloc[:-1].max()
            
            if dif_high < prev_difs * 0.9:
                return {'type': '顶背离', 'weaken': (prev_difs - dif_high) / prev_difs}
    else:
        price_low = df['low'].iloc[-1]
        prev_lows = df['low'].iloc[:-1].min()
        
        if price_low < prev_lows:
            dif_low = df['dif'].iloc[-1]
            prev_difs = df['dif'].iloc[:-1].min()
            
            if dif_low > prev_difs * 0.9:
                return {'type': '底背离', 'weaken': (dif_low - prev_difs) / abs(prev_difs)}
    
    return None


# ==================== 多指标综合分析 ====================

def analyze_multi_indicators(bars: pd.DataFrame, use_macd: bool = True) -> Dict:
    """
    多指标综合分析
    
    Returns:
        {
            'buy': 买入信号,
            'sell': 卖出信号,
            'direction': 方向,
            'trend': 趋势,
            'indicators': 技术指标,
            'score': 综合得分
        }
    """
    result = {
        'buy': None,
        'sell': None,
        'direction': '未知',
        'trend': '未知',
        'indicators': {},
        'score': 0.5
    }
    
    if len(bars) < 5:
        return result
    
    # 趋势判断
    if len(bars) >= 20:
        ma20 = bars['close'].rolling(20).mean().iloc[-1]
        ma60 = bars['close'].rolling(60).mean().iloc[-1] if len(bars) >= 60 else ma20
        if ma20 > ma60:
            result['trend'] = '上涨趋势'
            result['direction'] = '上涨'
        elif ma20 < ma60:
            result['trend'] = '下跌趋势'
            result['direction'] = '下跌'
        else:
            result['trend'] = '盘整'
    
    # 笔识别
    bi_list = identify_bi(bars)
    
    # 中枢
    zs = identify_zhongshu(bars)
    result['zhongshu'] = str(zs) if zs else None
    
    # MACD
    if use_macd:
        result['macd'] = calc_macd(bars)
    
    # 所有指标
    result['indicators'] = calc_all_indicators(bars)
    
    # 计算综合得分
    score = 0.5
    ind = result['indicators']
    
    # RSI (超卖买入, 超买卖出)
    if 'rsi' in ind:
        if ind['rsi'] < 30:
            score += 0.2  # 超卖
        elif ind['rsi'] > 70:
            score -= 0.2  # 超买
    
    # KDJ (金叉买入, 死叉卖出)
    if 'kdj_k' in ind and 'kdj_d' in ind:
        if ind['kdj_k'] < 20 and ind['kdj_d'] < 20:
            score += 0.15  # 超卖
        elif ind['kdj_k'] > 80 and ind['kdj_d'] > 80:
            score -= 0.15  # 超买
        if ind['kdj_k'] > ind['kdj_d'] and ind['kdj_j'] > 50:
            score += 0.1  # 金叉
        elif ind['kdj_k'] < ind['kdj_d'] and ind['kdj_j'] < 50:
            score -= 0.1  # 死叉
    
    # BOLL (下轨买入, 上轨卖出)
    if 'boll_pos' in ind:
        if ind['boll_pos'] < 0.2:
            score += 0.15  # 接近下轨
        elif ind['boll_pos'] > 0.8:
            score -= 0.15  # 接近上轨
    
    # CCI
    if 'cci' in ind:
        if ind['cci'] < -100:
            score += 0.15  # 超卖
        elif ind['cci'] > 100:
            score -= 0.15  # 超买
    
    # WR
    if 'wr' in ind:
        if ind['wr'] < 20:
            score -= 0.1  # 超买
        elif ind['wr'] > 80:
            score += 0.1  # 超卖
    
    # BIAS
    if 'bias' in ind:
        if ind['bias'] < -5:
            score += 0.1  # 负乖离大
        elif ind['bias'] > 5:
            score -= 0.1  # 正乖离大
    
    result['score'] = max(0, min(1, score))
    
    # 缠论背驰检测
    bi_beichi = None
    if len(bi_list) >= 2:
        current = bi_list[-1]
        prev = bi_list[-2]
        if current.direction == prev.direction:
            if current.force < prev.force * 0.8:
                bi_beichi = {'type': f"{result['direction']}背驰"}
    
    # 买入信号
    if result['direction'] == '下跌' or result['trend'] == '下跌趋势':
        # RSI超卖
        if ind.get('rsi', 50) < 30:
            result['buy'] = {'type': 'RSI超卖', 'confidence': 0.7, 'position': 0.4, 'reason': 'RSI<30超卖'}
        
        # KDJ超卖金叉
        if ind.get('kdj_k', 50) < 20 and ind.get('kdj_k', 0) > ind.get('kdj_d', 0):
            result['buy'] = {'type': 'KDJ超卖金叉', 'confidence': 0.75, 'position': 0.5, 'reason': 'KDJ超卖金叉'}
        
        # BOLL下轨
        if ind.get('boll_pos', 0.5) < 0.2:
            result['buy'] = {'type': 'BOLL下轨', 'confidence': 0.7, 'position': 0.5, 'reason': 'BOLL触及下轨'}
        
        # CCI超卖
        if ind.get('cci', 0) < -100:
            result['buy'] = {'type': 'CCI超卖', 'confidence': 0.7, 'position': 0.4, 'reason': 'CCI<-100超卖'}
        
        # 双重背离
        if bi_beichi and use_macd:
            macd_div = check_macd_divergence(bars, 'down')
            if macd_div:
                result['buy'] = {'type': '双重背离', 'confidence': 0.9, 'position': 0.8, 'reason': '笔背驰+MACD底背离'}
    
    # 上涨趋势买入
    elif result['direction'] == '上涨' or result['trend'] == '上涨趋势':
        # 二买
        if len(bi_list) >= 2 and bi_list[-1].direction == 'down':
            if bi_list[-1].low >= bi_list[-2].low * 0.99:
                result['buy'] = {'type': '二买', 'confidence': 0.8, 'position': 0.5, 'reason': '回调不破前低'}
        
        # MACD金叉
        if use_macd and result.get('macd'):
            m = result['macd']
            if m['macd'] > 0 and m['dif'] > m['dea']:
                result['buy'] = {'type': 'MACD金叉', 'confidence': 0.7, 'position': 0.5, 'reason': 'MACD水上金叉'}
        
        # KDJ金叉
        if ind.get('kdj_k', 0) > ind.get('kdj_d', 0) and ind.get('kdj_j', 0) > 50:
            result['buy'] = {'type': 'KDJ金叉', 'confidence': 0.65, 'position': 0.4, 'reason': 'KDJ金叉'}
    
    # 卖出信号
    if result['direction'] == '上涨' or result['trend'] == '上涨趋势':
        # RSI超买
        if ind.get('rsi', 50) > 70:
            result['sell'] = {'type': 'RSI超买', 'confidence': 0.7, 'reason': 'RSI>70超买'}
        
        # KDJ超买死叉
        if ind.get('kdj_k', 50) > 80 and ind.get('kdj_k', 0) < ind.get('kdj_d', 0):
            result['sell'] = {'type': 'KDJ超买死叉', 'confidence': 0.75, 'reason': 'KDJ超买死叉'}
        
        # BOLL上轨
        if ind.get('boll_pos', 0.5) > 0.8:
            result['sell'] = {'type': 'BOLL上轨', 'confidence': 0.7, 'reason': 'BOLL触及上轨'}
        
        # CCI超买
        if ind.get('cci', 0) > 100:
            result['sell'] = {'type': 'CCI超买', 'confidence': 0.7, 'reason': 'CCI>100超买'}
        
        # 双重背离
        if bi_beichi and use_macd:
            macd_div = check_macd_divergence(bars, 'up')
            if macd_div:
                result['sell'] = {'type': '双重背离', 'confidence': 0.9, 'reason': '笔背驰+MACD顶背离'}
    
    return result


# ==================== 策略类 ====================

class MultiIndicatorStrategy:
    """多指标综合策略"""
    
    def __init__(self,
                 stop_loss: float = 0.05,
                 profit_target: float = 0.15):
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        self.position = 0
        self.entry_price = 0
    
    def analyze(self, bars: pd.DataFrame) -> Dict:
        """分析信号"""
        result = analyze_multi_indicators(bars)
        
        action = 'hold'
        reason = ''
        position = 0
        
        # 卖出优先
        if self.position > 0:
            if result['sell']:
                action = 'sell'
                reason = result['sell']['reason']
            else:
                current = bars['close'].iloc[-1]
                profit = (current - self.entry_price) / self.entry_price
                
                if profit < -self.stop_loss:
                    action = 'sell'
                    reason = f'止损({profit:.1%})'
                elif profit > self.profit_target:
                    action = 'sell'
                    reason = f'止盈({profit:.1%})'
        
        # 买入
        elif result['buy']:
            action = 'buy'
            reason = result['buy']['reason']
            position = result['buy'].get('position', 0.5)
        
        return {
            'action': action,
            'reason': reason,
            'position': position,
            'direction': result['direction'],
            'trend': result['trend'],
            'score': result['score'],
            'buy': result['buy'],
            'sell': result['sell'],
            'indicators': result['indicators']
        }
    
    def execute(self, signal: Dict, price: float) -> Dict:
        """执行信号"""
        action = signal.get('action', 'hold')
        
        result = {'action': 'none', 'price': price}
        
        if action == 'buy' and self.position == 0:
            self.position = 1
            self.entry_price = price
            result['action'] = 'buy'
            result['position'] = signal.get('position', 0.5)
        
        elif action == 'sell' and self.position > 0:
            self.position = 0
            self.entry_price = 0
            result['action'] = 'sell'
        
        return result


# ==================== 测试 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("多指标综合策略测试")
    print("=" * 50)
    
    # 创建测试数据
    np.random.seed(42)
    prices = []
    base = 100
    for i in range(60):
        if i % 8 < 4:
            base += np.random.randn() * 0.8 + 0.5
        else:
            base -= np.random.randn() * 0.5
        prices.append(base + np.random.randn() * 0.3)
    
    bars = pd.DataFrame({
        'open': prices,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'close': prices,
        'volume': np.random.randint(100000, 1000000, 60)
    })
    
    # 指标计算
    print("\n【技术指标】")
    ind = calc_all_indicators(bars)
    print(f"RSI: {ind['rsi']:.1f}")
    print(f"KDJ: K={ind['kdj_k']:.1f}, D={ind['kdj_d']:.1f}, J={ind['kdj_j']:.1f}")
    print(f"BOLL: 上轨={ind['boll_ub']:.1f}, 下轨={ind['boll_lb']:.1f}, 位置={ind['boll_pos']:.2f}")
    print(f"CCI: {ind['cci']:.1f}")
    print(f"WR: {ind['wr']:.1f}")
    print(f"BIAS: {ind['bias']:.1f}")
    
    # 综合分析
    print("\n【综合分析】")
    result = analyze_multi_indicators(bars)
    print(f"方向: {result['direction']}")
    print(f"趋势: {result['trend']}")
    print(f"得分: {result['score']:.2f}")
    print(f"买入: {result['buy']}")
    print(f"卖出: {result['sell']}")
    
    # 策略
    print("\n【策略信号】")
    strategy = MultiIndicatorStrategy()
    signal = strategy.analyze(bars)
    print(f"动作: {signal['action']}")
    print(f"原因: {signal['reason']}")
    
    print("\n✅ 测试完成!")