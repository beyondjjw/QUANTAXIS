# -*- coding: utf-8 -*-
"""
缠论与MACD背离结合策略
双重确认: 缠论结构 + MACD背离

作者: beyondjjw
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


# ==================== MACD 计算 ====================

def calc_macd(bars: pd.DataFrame, 
              fast: int = 12, 
              slow: int = 26, 
              signal: int = 9) -> pd.DataFrame:
    """
    计算MACD指标
    
    Args:
        bars: K线数据
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    
    Returns:
        包含MACD指标的DataFrame
    """
    df = bars.copy()
    
    # 计算EMA
    df['ema_fast'] = df['close'].ewm(span=fast).mean()
    df['ema_slow'] = df['close'].ewm(span=slow).mean()
    
    # DIF = 快线 - 慢线
    df['dif'] = df['ema_fast'] - df['ema_slow']
    
    # DEA = DIF的EMA
    df['dea'] = df['dif'].ewm(span=signal).mean()
    
    # MACD柱 = (DIF - DEA) * 2
    df['macd'] = (df['dif'] - df['dea']) * 2
    
    return df


def get_latest_macd(bars: pd.DataFrame) -> Dict:
    """获取最新MACD值"""
    df = calc_macd(bars)
    return {
        'dif': df['dif'].iloc[-1],
        'dea': df['dea'].iloc[-1],
        'macd': df['macd'].iloc[-1],
        'dif_prev': df['dif'].iloc[-2],
        'dea_prev': df['dea'].iloc[-2]
    }


# ==================== MACD 背离检测 ====================

def check_macd_divergence(bars: pd.DataFrame, 
                          direction: str = 'up') -> Optional[Dict]:
    """
    检查MACD背离
    
    Args:
        bars: K线数据
        direction: 'up' 顶背离, 'down' 底背离
    
    Returns:
        背离信息或None
    """
    df = calc_macd(bars)
    
    if len(df) < 10:
        return None
    
    # 获取最近10个周期的最高/最低点
    if direction == 'up':
        # 顶背离: 价格创新高, MACD未创新高
        price_high_idx = df['high'].idxmax()
        macd_high_idx = df['dif'].idxmax()
        
        # 找到创新高的位置
        recent_high = df['high'].iloc[-1]
        prev_highs = df['high'].iloc[:-1]
        
        if len(prev_highs) > 0:
            max_prev_high = prev_highs.max()
            
            # 价格创新高
            if recent_high > max_prev_high:
                # 检查MACD是否创新高
                recent_dif = df['dif'].iloc[-1]
                prev_difs = df['dif'].iloc[:-1]
                max_prev_dif = prev_difs.max() if len(prev_difs) > 0 else 0
                
                # MACD未创新高 = 顶背离
                if recent_dif < max_prev_dif * 0.9:
                    return {
                        'type': '顶背离',
                        'price_high': recent_high,
                        'macd_high': recent_dif,
                        'prev_macd_high': max_prev_dif,
                        'weaken': (max_prev_dif - recent_dif) / max_prev_dif
                    }
    
    else:  # down
        # 底背离: 价格创新低, MACD未创新低
        recent_low = df['low'].iloc[-1]
        prev_lows = df['low'].iloc[:-1]
        
        if len(prev_lows) > 0:
            min_prev_low = prev_lows.min()
            
            if recent_low < min_prev_low:
                recent_dif = df['dif'].iloc[-1]
                prev_difs = df['dif'].iloc[:-1]
                min_prev_dif = prev_difs.min() if len(prev_difs) > 0 else 0
                
                if recent_dif > min_prev_dif * 0.9:  # 未创新低
                    return {
                        'type': '底背离',
                        'price_low': recent_low,
                        'macd_low': recent_dif,
                        'prev_macd_low': min_prev_dif,
                        'weaken': (recent_dif - min_prev_dif) / abs(min_prev_dif) if min_prev_dif != 0 else 0
                    }
    
    return None


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


def check_bi_beichi(bi_list: List[Bi]) -> Optional[Dict]:
    """笔背驰检测"""
    if len(bi_list) < 2:
        return None
    
    current = bi_list[-1]
    previous = bi_list[-2]
    
    if current.direction != previous.direction:
        return None
    
    if current.force < previous.force * 0.8:
        return {
            'type': f"{'上涨' if current.direction == 'up' else '下跌'}背驰",
            'current_force': current.force,
            'prev_force': previous.force
        }
    return None


# ==================== 双重背离判断 ====================

def check_double_divergence(bars: pd.DataFrame) -> Dict:
    """
    双重背离判断: 缠论背驰 + MACD背离
    
    Returns:
        {'buy': 买入信号, 'sell': 卖出信号, 'details': 详情}
    """
    result = {'buy': None, 'sell': None, 'details': {}}
    
    bi_list = identify_bi(bars)
    if len(bi_list) < 2:
        return result
    
    current_bi = bi_list[-1]
    
    # 1. 缠论笔背驰
    bi_beichi = check_bi_beichi(bi_list)
    
    # 2. MACD背离
    macd_direction = 'up' if current_bi.direction == 'up' else 'down'
    macd_div = check_macd_divergence(bars, macd_direction)
    
    # 3. 双重确认
    if current_bi.direction == 'up':
        # 检查顶背离
        if bi_beichi and '上涨' in str(bi_beichi.get('type', '')):
            if macd_div and macd_div['type'] == '顶背离':
                result['sell'] = {
                    'type': '双重顶背离',
                    'confidence': 0.95,
                    'bi_beichi': bi_beichi,
                    'macd_div': macd_div
                }
                result['details']['sell'] = '笔背驰 + MACD顶背离 = 强卖出信号'
            else:
                result['sell'] = {
                    'type': '笔背驰',
                    'confidence': 0.7,
                    'bi_beichi': bi_beichi
                }
                result['details']['sell'] = '笔背驰，可能见顶'
        elif macd_div and macd_div['type'] == '顶背离':
            result['sell'] = {
                'type': 'MACD顶背离',
                'confidence': 0.7,
                'macd_div': macd_div
            }
            result['details']['sell'] = 'MACD顶背离'
    
    else:  # down
        # 检查底背离
        if bi_beichi and '下跌' in str(bi_beichi.get('type', '')):
            if macd_div and macd_div['type'] == '底背离':
                result['buy'] = {
                    'type': '双重底背离',
                    'confidence': 0.95,
                    'bi_beichi': bi_beichi,
                    'macd_div': macd_div
                }
                result['details']['buy'] = '笔背驰 + MACD底背离 = 强买入信号'
            else:
                result['buy'] = {
                    'type': '笔背驰',
                    'confidence': 0.7,
                    'bi_beichi': bi_beichi
                }
                result['details']['buy'] = '笔背驰，可能见底'
        elif macd_div and macd_div['type'] == '底背离':
            result['buy'] = {
                'type': 'MACD底背离',
                'confidence': 0.7,
                'macd_div': macd_div
            }
            result['details']['buy'] = 'MACD底背离'
    
    return result


# ==================== 完整策略 ====================

class ChanMacdStrategy:
    """
    缠论 + MACD背离策略
    
    双重确认买卖点
    """
    
    def __init__(self, 
                 stop_loss: float = 0.05,
                 profit_target: float = 0.15):
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        self.position = 0
        self.entry_price = 0
    
    def analyze(self, bars: pd.DataFrame) -> Dict:
        """分析并生成信号"""
        result = {
            'action': 'hold',
            'reason': '',
            'confidence': 0.5,
            'macd': get_latest_macd(bars)
        }
        
        # 双重背离检查
        div_result = check_double_divergence(bars)
        
        # 卖出信号
        if div_result['sell']:
            sell_info = div_result['sell']
            result['action'] = 'sell' if self.position > 0 else 'watch'
            result['reason'] = div_result['details'].get('sell', '')
            result['confidence'] = sell_info['confidence']
            return result
        
        # 买入信号
        if div_result['buy'] and self.position == 0:
            buy_info = div_result['buy']
            result['action'] = 'buy'
            result['reason'] = div_result['details'].get('buy', '')
            result['confidence'] = buy_info['confidence']
            return result
        
        # 持仓检查
        if self.position > 0:
            current = bars['close'].iloc[-1]
            profit = (current - self.entry_price) / self.entry_price
            
            # 止损
            if profit < -self.stop_loss:
                result['action'] = 'sell'
                result['reason'] = f'止损({profit:.1%})'
                return result
            
            # 止盈
            if profit > self.profit_target:
                result['action'] = 'sell'
                result['reason'] = f'止盈({profit:.1%})'
                return result
        
        return result
    
    def execute(self, signal: Dict, price: float) -> Dict:
        """执行信号"""
        action = signal.get('action', 'hold')
        
        result = {'action': 'none', 'price': price}
        
        if action == 'buy' and self.position == 0:
            self.position = 1
            self.entry_price = price
            result['action'] = 'buy'
        
        elif action == 'sell' and self.position > 0:
            self.position = 0
            self.entry_price = 0
            result['action'] = 'sell'
        
        return result


# ==================== 测试 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("缠论 + MACD背离策略测试")
    print("=" * 50)
    
    # 创建测试数据 (模拟顶背离)
    np.random.seed(42)
    n = 50
    
    # 模拟上涨后顶背离
    prices = []
    base = 100
    for i in range(n):
        if i < 30:
            base += np.random.randn() * 0.5 + 0.3  # 上涨
        else:
            base += np.random.randn() * 0.3 - 0.1  # 滞涨
        prices.append(base)
    
    bars = pd.DataFrame({
        'open': prices,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n)
    })
    
    # MACD测试
    print("\n【MACD指标】")
    macd = get_latest_macd(bars)
    print(f"DIF: {macd['dif']:.4f}")
    print(f"DEA: {macd['dea']:.4f}")
    print(f"MACD: {macd['macd']:.4f}")
    
    # 背离检测
    print("\n【背离检测】")
    bi_list = identify_bi(bars)
    print(f"笔数量: {len(bi_list)}")
    
    bi_beichi = check_bi_beichi(bi_list)
    print(f"笔背驰: {bi_beichi}")
    
    macd_div_up = check_macd_divergence(bars, 'up')
    print(f"MACD顶背离: {macd_div_up}")
    
    # 双重背离
    print("\n【双重背离判断】")
    div_result = check_double_divergence(bars)
    print(f"买入信号: {div_result['buy']}")
    print(f"卖出信号: {div_result['sell']}")
    print(f"详情: {div_result['details']}")
    
    # 策略测试
    print("\n【策略信号】")
    strategy = ChanMacdStrategy()
    signal = strategy.analyze(bars)
    print(f"动作: {signal['action']}")
    print(f"原因: {signal['reason']}")
    print(f"置信度: {signal['confidence']}")
    
    print("\n✅ 测试完成!")