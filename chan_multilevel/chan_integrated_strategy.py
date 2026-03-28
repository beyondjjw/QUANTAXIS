# -*- coding: utf-8 -*-
"""
缠论综合交易策略 - 统一买入卖出信号
整合: 多级别联立 + MACD背离 + 30分钟短线

作者: beyondjjw
版本: 3.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


# ==================== 笔识别 ====================

class Bi:
    """笔结构"""
    def __init__(self, direction: str, high: float, low: float):
        self.direction = direction  # 'up' / 'down'
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


# ==================== 综合信号分析 ====================

def analyze_buy_sell_signals(bars: pd.DataFrame, 
                            use_macd: bool = True,
                            use_zhongshu: bool = True) -> Dict:
    """
    综合买入卖出信号分析
    
    整合: 笔结构 + 中枢 + MACD背离
    
    Returns:
        {
            'buy': {'type': str, 'confidence': float, 'reason': str},
            'sell': {'type': str, 'confidence': float, 'reason': str},
            'direction': str,
            'trend': str,
            'macd': dict,
            'zhongshu': str
        }
    """
    result = {
        'buy': None,
        'sell': None,
        'direction': '未知',
        'trend': '未知',
        'macd': None,
        'zhongshu': None
    }
    
    if len(bars) < 5:
        return result
    
    # 1. 趋势判断 (优先)
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
    
    # 2. 笔识别
    bi_list = identify_bi(bars)
    
    # 3. 中枢
    if use_zhongshu:
        zs = identify_zhongshu(bars)
        result['zhongshu'] = str(zs) if zs else None
    
    # 4. MACD
    if use_macd:
        result['macd'] = calc_macd(bars)
    
    # 5. 笔背驰检测
    bi_beichi = None
    if len(bi_list) >= 2:
        current = bi_list[-1]
        prev = bi_list[-2]
        if current.direction == prev.direction:
            if current.force < prev.force * 0.8:
                bi_beichi = {'type': f"{result['direction']}背驰", 'weaken': (prev.force - current.force) / prev.force}
    
    # 6. 买入信号 (下跌趋势 or 底背离)
    if result['direction'] == '下跌' or result['trend'] == '下跌趋势':
        # 底分型
        if len(bars) >= 3:
            mid_low = bars['low'].iloc[1]
            if mid_low < bars['low'].iloc[0] and mid_low < bars['low'].iloc[2]:
                result['buy'] = {
                    'type': '底分型',
                    'confidence': 0.6,
                    'position': 0.3,
                    'reason': '底分型买入'
                }
        
        # 二买: 连续两笔下跌，第二笔低点不低于第一笔
        if len(bi_list) >= 2:
            if bi_list[-1].direction == 'down' and bi_list[-1].low >= bi_list[-2].low * 0.99:
                result['buy'] = {
                    'type': '二买',
                    'confidence': 0.8,
                    'position': 0.5,
                    'reason': '回调不破前低(二买)'
                }
        
        # MACD底背离
        if use_macd:
            macd_div = check_macd_divergence(bars, 'down')
            if macd_div:
                result['buy'] = {
                    'type': 'MACD底背离',
                    'confidence': 0.7,
                    'position': 0.4,
                    'reason': 'MACD底背离'
                }
        
        # 双重背离
        if bi_beichi and use_macd:
            macd_div = check_macd_divergence(bars, 'down')
            if macd_div:
                result['buy'] = {
                    'type': '双重底背离',
                    'confidence': 0.95,
                    'position': 0.8,
                    'reason': '笔背驰+MACD底背离'
                }
    
    # 7. 上涨趋势中的回调买入 (二买/三买)
    elif result['direction'] == '上涨' or result['trend'] == '上涨趋势':
        # 上涨趋势中的回调不破前低 = 二买
        if len(bi_list) >= 2:
            if bi_list[-1].direction == 'down' and bi_list[-1].low >= bi_list[-2].low * 0.99:
                result['buy'] = {
                    'type': '二买',
                    'confidence': 0.8,
                    'position': 0.5,
                    'reason': '上涨回调不破前低(二买)'
                }
        
        # 底分型 (小幅反弹)
        elif len(bars) >= 3:
            mid_low = bars['low'].iloc[1]
            if mid_low < bars['low'].iloc[0] and mid_low < bars['low'].iloc[2]:
                result['buy'] = {
                    'type': '底分型',
                    'confidence': 0.5,
                    'position': 0.3,
                    'reason': '上涨中底分型反弹'
                }
        
        # MACD底背离 (回调中金叉)
        if use_macd:
            macd = result['macd']
            if macd and macd['macd'] > 0 and macd['dea'] > 0:
                result['buy'] = {
                    'type': 'MACD金叉',
                    'confidence': 0.6,
                    'position': 0.4,
                    'reason': 'MACD水上金叉'
                }
        
        # 三买: 突破中枢后回调不破ZG
        if use_zhongshu and result['zhongshu']:
            current_price = bars['close'].iloc[-1]
            zs = identify_zhongshu(bars)
            if zs and current_price > zs.zg:
                if current_price >= zs.zg * 0.99:
                    result['buy'] = {
                        'type': '三买',
                        'confidence': 0.75,
                        'position': 0.6,
                        'reason': '突破中枢后回调不破ZG'
                    }
    
    # 8. 卖出信号 (上涨趋势)
    if result['direction'] == '上涨' or result['trend'] == '上涨趋势':
        # 顶分型
        if len(bars) >= 3:
            mid_high = bars['high'].iloc[1]
            if mid_high > bars['high'].iloc[0] and mid_high > bars['high'].iloc[2]:
                result['sell'] = {
                    'type': '顶分型',
                    'confidence': 0.6,
                    'reason': '顶分型卖出'
                }
        
        # 背驰
        if bi_beichi:
            result['sell'] = {
                'type': '笔背驰',
                'confidence': 0.7,
                'reason': '笔背驰可能见顶'
            }
        
        # MACD顶背离
        if use_macd:
            macd_div = check_macd_divergence(bars, 'up')
            if macd_div:
                result['sell'] = {
                    'type': 'MACD顶背离',
                    'confidence': 0.7,
                    'reason': 'MACD顶背离'
                }
        
        # 双重背离
        if bi_beichi and use_macd:
            macd_div = check_macd_divergence(bars, 'up')
            if macd_div:
                result['sell'] = {
                    'type': '双重顶背离',
                    'confidence': 0.95,
                    'reason': '笔背驰+MACD顶背离'
                }
    
    return result


# ==================== 完整策略类 ====================

class ChanIntegratedStrategy:
    """
    缠论综合交易策略
    
    统一买入卖出信号
    """
    
    def __init__(self,
                 # 多级别配置
                 monthly_data: pd.DataFrame = None,
                 # 止损止盈
                 stop_loss: float = 0.05,
                 profit_target: float = 0.15,
                 # 功能开关
                 use_macd: bool = True,
                 use_zhongshu: bool = True,
                 # 30分钟短线模式
                 short_mode: bool = False):
        self.monthly_data = monthly_data
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        self.use_macd = use_macd
        self.use_zhongshu = use_zhongshu
        self.short_mode = short_mode
        
        # 持仓
        self.position = 0
        self.entry_price = 0
    
    def get_month_direction(self) -> str:
        """月线牛熊判断"""
        if self.monthly_data is None or len(self.monthly_data) < 60:
            return '未知'
        
        close_series = self.monthly_data['close']
        if not isinstance(close_series, pd.Series) or len(close_series) < 12:
            return '未知'
        
        ma12 = close_series.rolling(12).mean().iloc[-1]
        ma60 = close_series.rolling(60).mean().iloc[-1]
        
        if pd.isna(ma12) or pd.isna(ma60):
            return '未知'
        
        return '牛市' if ma12 > ma60 else '熊市'
    
    def analyze(self, bars: pd.DataFrame) -> Dict:
        """分析信号"""
        # 多级别限制
        if not self.short_mode and self.monthly_data is not None:
            month_dir = self.get_month_direction()
            if month_dir == '熊市':
                return {
                    'action': 'watch',
                    'reason': '月线熊市，不开新仓',
                    'month_direction': month_dir
                }
        
        # 综合分析
        result = analyze_buy_sell_signals(bars, self.use_macd, self.use_zhongshu)
        
        # 决定动作
        action = 'hold'
        reason = ''
        position = 0
        
        # ===== 仓位控制 (根据趋势和月线) =====
        trend = result.get('trend', '未知')
        
        # 获取月线方向
        has_monthly = isinstance(self.monthly_data, pd.DataFrame) and len(self.monthly_data) > 0
        month_dir = self.get_month_direction() if has_monthly else '未知'
        
        # 基础仓位
        if month_dir == '牛市':
            base_position = 0.8
        elif month_dir == '熊市':
            base_position = 0.2
        else:
            base_position = 0.5
        
        # 根据趋势调整
        if trend == '上涨趋势':
            base_position = min(base_position, 0.8)
        elif trend == '下跌趋势':
            base_position = min(base_position, 0.3)
        
        # 卖出优先 (持仓中)
        if self.position > 0:
            if result['sell']:
                action = 'sell'
                reason = result['sell']['reason']
            else:
                # 止损检查
                current = bars['close'].iloc[-1]
                profit = (current - self.entry_price) / self.entry_price
                
                if profit < -self.stop_loss:
                    action = 'sell'
                    reason = f'止损({profit:.1%})'
                elif profit > self.profit_target:
                    action = 'sell'
                    reason = f'止盈({profit:.1%})'
        
        # 买入 (空仓中)
        elif result['buy']:
            # 使用信号中的仓位，但不超过基础仓位
            signal_position = result['buy'].get('position', 0.5)
            position = min(signal_position, base_position)
            
            action = 'buy'
            reason = result['buy']['reason']
        
        return {
            'action': action,
            'reason': reason,
            'position': position,
            'direction': result['direction'],
            'trend': result['trend'],
            'buy': result['buy'],
            'sell': result['sell'],
            'macd': result['macd'],
            'zhongshu': result['zhongshu']
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
    print("缠论综合交易策略测试")
    print("=" * 50)
    
    # 测试数据
    np.random.seed(42)
    n = 60
    
    # 模拟下跌后反弹
    prices = []
    base = 100
    for i in range(n):
        if i < 40:
            base -= np.random.randn() * 0.5  # 下跌
        else:
            base += np.random.randn() * 0.3  # 反弹
        prices.append(base)
    
    bars = pd.DataFrame({
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n)
    })
    
    # 综合分析
    print("\n【综合信号分析】")
    result = analyze_buy_sell_signals(bars)
    print(f"方向: {result['direction']}")
    print(f"趋势: {result['trend']}")
    print(f"中枢: {result['zhongshu']}")
    print(f"MACD: {result['macd']}")
    print(f"买入: {result['buy']}")
    print(f"卖出: {result['sell']}")
    
    # 策略
    print("\n【策略信号】")
    strategy = ChanIntegratedStrategy()
    signal = strategy.analyze(bars)
    print(f"动作: {signal['action']}")
    print(f"原因: {signal['reason']}")
    print(f"仓位: {signal['position']}")
    
    print("\n✅ 测试完成!")