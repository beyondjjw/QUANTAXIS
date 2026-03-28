# -*- coding: utf-8 -*-
"""
30分钟级别短线波段策略
操作周期: 30分钟为主 + 5分钟精准入场

作者: beyondjjw
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


# ==================== 笔识别 ====================

class Bi:
    """笔结构"""
    def __init__(self, direction: str, high: float, low: float, 
                 start_idx: int = 0, end_idx: int = 0):
        self.direction = direction  # 'up' / 'down'
        self.high = high
        self.low = low
        self.start_idx = start_idx
        self.end_idx = end_idx
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
        
        # 顶分型
        if curr['high'] >= prev['high'] and curr['high'] >= next_['high']:
            bits.append(Bi('up', curr['high'], prev['low'], i-1, i))
        # 底分型
        elif curr['low'] <= prev['low'] and curr['low'] <= next_['low']:
            bits.append(Bi('down', prev['high'], curr['low'], i-1, i))
    
    # 合并相邻同方向笔
    merged = []
    for b in bits:
        if not merged:
            merged.append(b)
        elif b.direction == merged[-1].direction:
            merged[-1] = Bi(b.direction, 
                          max(merged[-1].high, b.high), 
                          min(merged[-1].low, b.low),
                          merged[-1].start_idx, b.end_idx)
        else:
            merged.append(b)
    
    return merged


def is_bottom_pattern(bars: pd.DataFrame) -> bool:
    """底分型确认"""
    if len(bars) < 3:
        return False
    
    # 中间K线低点最低
    low = bars['low'].iloc[1]
    return low < bars['low'].iloc[0] and low < bars['low'].iloc[2]


def is_top_pattern(bars: pd.DataFrame) -> bool:
    """顶分型确认"""
    if len(bars) < 3:
        return False
    
    # 中间K线高点最高
    high = bars['high'].iloc[1]
    return high > bars['high'].iloc[0] and high > bars['high'].iloc[2]


# ==================== 中枢识别 ====================

class ZhongShu:
    """中枢"""
    def __init__(self, zg: float, zd: float):
        self.zg = zg  # 上沿
        self.zd = zd  # 下沿
    
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


# ==================== 背驰检测 ====================

def check_beichi(bi_list: List[Bi]) -> Optional[Dict]:
    """背驰检测"""
    if len(bi_list) < 2:
        return None
    
    current = bi_list[-1]
    previous = bi_list[-2]
    
    if current.direction != previous.direction:
        return None
    
    # 力度对比
    if current.force < previous.force * 0.8:
        return {
            'type': f"{'上涨' if current.direction == 'up' else '下跌'}背驰",
            'weaken': (previous.force - current.force) / previous.force
        }
    return None


# ==================== 30分钟策略 ====================

class Min30ShortStrategy:
    """
    30分钟短线波段策略
    
    规则:
    - 只做30分钟笔完整行情
    - 3%止损 + 8%止盈
    - 日交易不超过3次
    """
    
    def __init__(self,
                 stop_loss: float = 0.03,      # 3%止损
                 profit_target: float = 0.08,   # 8%止盈
                 max_daily_trades: int = 3):    # 日交易≤3次
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        self.max_daily_trades = max_daily_trades
        
        # 持仓
        self.position = 0
        self.entry_price = 0
        
        # 交易统计
        self.daily_trades = 0
        self.today_trades = 0
    
    def get_trend(self, bars: pd.DataFrame) -> str:
        """趋势判断"""
        if len(bars) < 60:
            return '构建中'
        
        ma20 = bars['close'].rolling(20).mean().iloc[-1]
        ma60 = bars['close'].rolling(60).mean().iloc[-1]
        
        if ma20 > ma60:
            return '上涨趋势'
        elif ma20 < ma60:
            return '下跌趋势'
        return '盘整'
    
    def get_direction(self, bars: pd.DataFrame) -> str:
        """方向判断 (EMA)"""
        if len(bars) < 26:
            return '未知'
        
        ema12 = bars['close'].ewm(span=12).mean().iloc[-1]
        ema26 = bars['close'].ewm(span=26).mean().iloc[-1]
        
        return '上涨' if ema12 > ema26 else '下跌'
    
    def get_position_limit(self, trend: str) -> float:
        """仓位限制"""
        if trend == '上涨趋势':
            return 0.8
        elif trend == '下跌趋势':
            return 0.2
        return 0.5  # 盘整
    
    def check_buy_point(self, bars_30min: pd.DataFrame, 
                        bars_5min: pd.DataFrame = None) -> Optional[Dict]:
        """检查买点"""
        bi_list = identify_bi(bars_30min)
        
        if len(bi_list) < 1:
            return None
        
        # 底分型买
        if is_bottom_pattern(bars_30min.tail(3)):
            return {'type': '底分型买', 'position': 0.3, 'confidence': 0.6}
        
        # 二买: 回调不破前低
        if len(bi_list) >= 2:
            last_bi = bi_list[-1]
            prev_bi = bi_list[-2]
            
            if last_bi.direction == 'down' and last_bi.low >= prev_bi.low * 0.99:
                return {'type': '二买', 'position': 0.5, 'confidence': 0.8}
        
        # 三买: 突破中枢后回调不破
        zs = identify_zhongshu(bars_30min)
        if zs:
            current = bars_30min['close'].iloc[-1]
            direction = self.get_direction(bars_30min)
            if direction == '上涨' and current > zs.zg:
                if current >= zs.zg * 0.99:
                    return {'type': '三买', 'position': 0.2, 'confidence': 0.7}
        
        return None
    
    def check_sell_point(self, bars_30min: pd.DataFrame) -> Optional[Dict]:
        """检查卖点"""
        if self.position == 0:
            return None
        
        bi_list = identify_bi(bars_30min)
        
        # 顶分型卖
        if is_top_pattern(bars_30min.tail(3)):
            return {'type': '顶分型卖', 'confidence': 0.7}
        
        # 背驰卖
        beichi = check_beichi(bi_list)
        if beichi and '上涨' in str(beichi.get('type', '')):
            return {'type': '背驰卖', 'confidence': 0.8}
        
        return None
    
    def analyze(self, bars_30min: pd.DataFrame, 
                bars_15min: pd.DataFrame = None,
                bars_5min: pd.DataFrame = None) -> Dict:
        """分析并生成信号"""
        result = {
            'action': 'hold',
            'reason': '',
            'position': 0,
            'trend': '未知',
            'direction': '未知',
            'buy_point': None,
            'sell_point': None
        }
        
        # 基本分析
        trend = self.get_trend(bars_30min)
        direction = self.get_direction(bars_30min)
        
        result['trend'] = trend
        result['direction'] = direction
        result['position_limit'] = self.get_position_limit(trend)
        
        # 检查是否超过日交易限制
        if self.daily_trades >= self.max_daily_trades:
            result['reason'] = '日交易次数已达上限'
            return result
        
        # 检查卖点 (持仓中)
        sell_point = self.check_sell_point(bars_30min)
        if sell_point:
            result['action'] = 'sell'
            result['reason'] = f"30分{sell_point['type']}"
            result['sell_point'] = sell_point
            return result
        
        # 止损检查
        if self.position > 0:
            current_price = bars_30min['close'].iloc[-1]
            loss = (current_price - self.entry_price) / self.entry_price
            
            if loss < -self.stop_loss:
                result['action'] = 'sell'
                result['reason'] = f'止损({loss:.1%})'
                return result
            
            # 止盈检查
            if loss > self.profit_target:
                result['action'] = 'sell'
                result['reason'] = f'止盈({loss:.1%})'
                result['sell_point'] = {'type': '止盈', 'confidence': 1.0}
                return result
        
        # 检查买点 (空仓)
        if self.position == 0:
            # 15分钟方向验证
            if bars_15min is not None:
                dir_15min = self.get_direction(bars_15min)
                if dir_15min != direction:
                    result['reason'] = '15分钟方向与30分钟不一致'
                    return result
            
            buy_point = self.check_buy_point(bars_30min, bars_5min)
            if buy_point:
                result['action'] = 'buy'
                result['reason'] = f"30分{buy_point['type']}"
                result['position'] = buy_point['position']
                result['buy_point'] = buy_point
                return result
        
        return result
    
    def execute(self, signal: Dict, current_price: float) -> Dict:
        """执行信号"""
        action = signal.get('action', 'hold')
        
        result = {
            'action': 'none',
            'price': current_price,
            'volume': 0,
            'reason': signal.get('reason', '')
        }
        
        if action == 'buy' and self.position == 0:
            position = signal.get('position', 0.5)
            volume = position / current_price
            
            self.position = volume
            self.entry_price = current_price
            self.daily_trades += 1
            
            result['action'] = 'buy'
            result['volume'] = volume
            result['position'] = position
        
        elif action == 'sell' and self.position > 0:
            result['action'] = 'sell'
            result['volume'] = self.position
            
            self.position = 0
            self.entry_price = 0
        
        return result
    
    def reset_daily(self):
        """重置日交易计数"""
        self.daily_trades = 0


# ==================== 测试 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("30分钟短线波段策略测试")
    print("=" * 50)
    
    # 模拟30分钟数据
    np.random.seed(42)
    n = 100
    
    # 30分钟数据 (模拟上涨趋势)
    prices = []
    base = 100
    for i in range(n):
        if i < 30:
            base += np.random.randn() * 0.5
        elif i < 60:
            base -= np.random.randn() * 0.3  # 回调
        else:
            base += np.random.randn() * 0.4  # 上涨
        prices.append(base)
    
    bars_30min = pd.DataFrame({
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n)
    })
    
    # 15分钟数据
    bars_15min = bars_30min.copy()
    
    # 5分钟数据
    bars_5min = bars_30min.copy()
    
    # 创建策略
    strategy = Min30ShortStrategy()
    
    # 分析
    print("\n【30分钟分析】")
    print(f"趋势: {strategy.get_trend(bars_30min)}")
    print(f"方向: {strategy.get_direction(bars_30min)}")
    
    bi_list = identify_bi(bars_30min)
    print(f"笔数量: {len(bi_list)}")
    
    zs = identify_zhongshu(bars_30min)
    print(f"中枢: {zs}")
    
    beichi = check_beichi(bi_list)
    print(f"背驰: {beichi}")
    
    # 交易信号
    print("\n【交易信号】")
    signal = strategy.analyze(bars_30min, bars_15min, bars_5min)
    print(f"动作: {signal['action']}")
    print(f"原因: {signal['reason']}")
    print(f"仓位: {signal['position']}")
    
    # 买点检测
    buy_point = strategy.check_buy_point(bars_30min, bars_5min)
    print(f"买点: {buy_point}")
    
    # 执行
    print("\n【执行结果】")
    result = strategy.execute(signal, 100.0)
    print(result)
    
    print("\n✅ 30分钟策略测试完成!")