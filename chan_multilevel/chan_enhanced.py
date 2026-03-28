# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略 - 增强版
包含: 中枢识别、买卖点判断、精确背驰检测

作者: beyondjjw
版本: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict


# ==================== 中枢识别 ====================

class ZhongShu:
    """
    中枢识别器
    
    中枢 = 至少三段重叠区域
    """
    
    def __init__(self):
        self.high = 0
        self.low = 0
        self.elements = []  # 构成中枢的笔/段
        self.type = None    # '上涨中枢' / '下跌中枢'
    
    def __repr__(self):
        return f"中枢(高点:{self.high:.2f}, 低点:{self.low:.2f}, 类型:{self.type})"


def identify_zhongshu(bars: pd.DataFrame, min_bars: int = 5) -> Optional[ZhongShu]:
    """
    识别中枢
    
    Args:
        bars: K线数据
        min_bars: 最小K线数
        
    Returns:
        ZhongShu 实例或 None
    """
    if len(bars) < min_bars * 3:
        return None
    
    # 简化: 使用高低点构建
    highs = bars['high'].values
    lows = bars['low'].values
    
    # 寻找重叠区域
    candidates = []
    for i in range(len(bars) - 4):
        # 三段重叠
        h1, h2, h3 = highs[i:i+3]
        l1, l2, l3 = lows[i:i+3]
        
        high = min(h1, h2, h3)
        low = max(l1, l2, l3)
        
        if high > low:  # 有重叠
            candidates.append((low, high))
    
    if not candidates:
        return None
    
    # 合并重叠区域
    candidates.sort(key=lambda x: x[0])
    merged = []
    for c in candidates:
        if not merged or c[0] > merged[-1][1]:
            merged.append(c)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]))
    
    if not merged:
        return None
    
    # 取第一个中枢
    zg = merged[0][1]
    zd = merged[0][0]
    
    zs = ZhongShu()
    zs.high = zg
    zs.low = zd
    
    # 判断类型
    if len(bars) >= 2:
        if bars['close'].iloc[-1] > bars['open'].iloc[-1]:
            zs.type = '上涨中枢'
        else:
            zs.type = '下跌中枢'
    
    return zs


def is_above_zhongshu(price: float, zs: ZhongShu) -> bool:
    """价格在中枢上方"""
    return price > zs.high if zs else False


def is_below_zhongshu(price: float, zs: ZhongShu) -> bool:
    """价格在中枢下方"""
    return price < zs.low if zs else False


def is_in_zhongshu(price: float, zs: ZhongShu) -> bool:
    """价格在中枢内"""
    return zs.low <= price <= zs.high if zs else False


# ==================== 笔识别 ====================

class Bi:
    """
    笔识别
    
    笔 = 相邻的顶分型和底分型之间
    """
    
    def __init__(self, start_idx: int, end_idx: int, 
                 direction: str, high: float, low: float):
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.direction = direction  # 'up' / 'down'
        self.high = high
        self.low = low
        self.elements = []  # 包含的K线
    
    def __repr__(self):
        return f"笔({self.direction}, 高:{self.high:.2f}, 低:{self.low:.2f})"


# ==================== 简化笔识别 ====================

def identify_bi(bars: pd.DataFrame) -> List[Bi]:
    """
    简化笔识别 - 基于包含关系
    
    Args:
        bars: K线数据
        
    Returns:
        笔列表
    """
    if len(bars) < 5:
        return []
    
    bits = []
    
    # 使用简化逻辑: 连续上涨/下跌形成笔
    for i in range(1, len(bars) - 1):
        curr = bars.iloc[i]
        prev = bars.iloc[i-1]
        next_ = bars.iloc[i+1]
        
        # 寻找顶分型
        if curr['high'] >= prev['high'] and curr['high'] >= next_['high']:
            if len(bits) > 0 and bits[-1].direction == 'down':
                # 完成下跌笔
                bits.append(Bi(bits[-1].end_idx, i, 'down', prev['high'], bits[-1].low))
            bits.append(Bi(i, i, 'up', curr['high'], prev['low']))
        
        # 寻找底分型
        elif curr['low'] <= prev['low'] and curr['low'] <= next_['low']:
            if len(bits) > 0 and bits[-1].direction == 'up':
                # 完成上涨笔
                bits.append(Bi(bits[-1].end_idx, i, 'up', curr['low'], bits[-1].high))
            bits.append(Bi(i, i, 'down', prev['high'], curr['low']))
    
    # 合并相邻同方向笔
    merged = []
    for b in bits:
        if not merged:
            merged.append(b)
        elif b.direction == merged[-1].direction:
            # 合并
            merged[-1] = Bi(merged[-1].start_idx, b.end_idx, b.direction,
                          max(merged[-1].high, b.high), min(merged[-1].low, b.low))
        else:
            merged.append(b)
    
    return merged


# ==================== 背驰检测 ====================

def check_beichi(bars: pd.DataFrame, bi_list: List[Bi]) -> Optional[Dict]:
    """
    精确背驰检测
    
    Args:
        bars: K线数据
        bi_list: 笔列表
        
    Returns:
        背驰信息或 None
    """
    if len(bi_list) < 2:
        return None
    
    # 比较最近两笔的力度
    last_bi = bi_list[-1]
    prev_bi = bi_list[-2]
    
    if last_bi.direction != prev_bi.direction:
        return None
    
    # 计算力度 (用涨跌幅近似)
    if last_bi.direction == 'up':
        current_force = (last_bi.high - last_bi.low) / last_bi.low
        prev_force = (prev_bi.high - prev_bi.low) / prev_bi.low
        
        if current_force < prev_force * 0.8:
            return {
                'type': '上涨背驰',
                'current': current_force,
                'prev': prev_force,
                'level': abs(current_force - prev_force) / prev_force
            }
    else:
        current_force = (prev_bi.low - last_bi.low) / prev_bi.low
        prev_force = (prev_bi.high - prev_bi.low) / prev_bi.low
        
        if current_force < prev_force * 0.8:
            return {
                'type': '下跌背驰',
                'current': current_force,
                'prev': prev_force,
                'level': abs(current_force - prev_force) / prev_force
            }
    
    return None


def check_zhongshu_beichi(bars: pd.DataFrame, zs: ZhongShu) -> Optional[Dict]:
    """
    中枢背驰检测
    
    比较进入段和离开段的力度
    
    Args:
        bars: K线数据
        zs: 中枢
        
    Returns:
        背驰信息或 None
    """
    if not zs or len(bars) < 20:
        return None
    
    # 简化: 比较中枢前后两段
    # 进入段: 中枢前的一段
    # 离开段: 中枢后的一段
    
    mid = len(bars) // 2
    
    # 进入段
    entry = bars.iloc[:mid]
    if len(entry) < 5:
        return None
    
    entry_change = (entry['close'].iloc[-1] - entry['close'].iloc[0]) / entry['close'].iloc[0]
    
    # 离开段
    exit_ = bars.iloc[mid:]
    if len(exit_) < 5:
        return None
    
    exit_change = (exit_['close'].iloc[-1] - exit_['close'].iloc[0]) / exit_['close'].iloc[0]
    
    # 判断背驰
    if zs.type == '上涨中枢':
        if exit_change > 0 and exit_change < entry_change * 0.8:
            return {
                'type': '中枢背驰(上涨)',
                'entry': entry_change,
                'exit': exit_change
            }
    elif zs.type == '下跌中枢':
        if exit_change < 0 and abs(exit_change) < abs(entry_change) * 0.8:
            return {
                'type': '中枢背驰(下跌)',
                'entry': entry_change,
                'exit': exit_change
            }
    
    return None


# ==================== 买卖点判断 ====================

class BuySellPoints:
    """
    买卖点判断
    
    一买: 大级别下跌背驰终点
    二买: 大级别上涨中，小级别回调不破前低
    三买: 大级别上涨回调不破中枢上沿
    
    一卖: 大级别上涨背驰
    二卖: 大级别下跌反弹高点
    三卖: 大级别下跌反弹破中枢下沿
    """
    
    @staticmethod
    def first_buy(bars: pd.DataFrame, bi_list: List[Bi], 
                  beichi: Dict) -> Optional[Dict]:
        """
        一买: 下跌背驰终点
        
        条件:
        - 大级别下跌趋势
        - 出现背驰
        - 背驰段创新低
        """
        if not beichi:
            return None
        
        if '下跌' in beichi.get('type', ''):
            return {
                'type': '一买',
                'price': bars['close'].iloc[-1],
                'reason': '下跌背驰终点',
                'confidence': 0.8
            }
        
        return None
    
    @staticmethod
    def second_buy(bars: pd.DataFrame, big_direction: str,
                   small_bi: Bi, prev_low: float) -> Optional[Dict]:
        """
        二买: 回调不破前低
        
        条件:
        - 大级别上涨
        - 小级别回调结束
        - 不破前低
        """
        if big_direction != '上涨':
            return None
        
        if small_bi and small_bi.direction == 'down':
            if small_bi.low >= prev_low * 0.99:  # 不破前低
                return {
                    'type': '二买',
                    'price': bars['close'].iloc[-1],
                    'reason': '回调不破前低',
                    'confidence': 0.7
                }
        
        return None
    
    @staticmethod
    def third_buy(bars: pd.DataFrame, zs: ZhongShu) -> Optional[Dict]:
        """
        三买: 突破中枢后回调不破
        
        条件:
        - 之前有中枢
        - 突破中枢上沿
        - 回调不破中枢上沿
        """
        if not zs:
            return None
        
        current_price = bars['close'].iloc[-1]
        
        # 突破中枢
        if current_price > zs.high:
            # 回调检查
            if current_price >= zs.high * 0.99:
                return {
                    'type': '三买',
                    'price': current_price,
                    'reason': '突破中枢后回调不破',
                    'confidence': 0.75
                }
        
        return None
    
    @staticmethod
    def first_sell(bars: pd.DataFrame, bi_list: List[Bi],
                   beichi: Dict) -> Optional[Dict]:
        """
        一卖: 上涨背驰
        """
        if not beichi:
            return None
        
        if '上涨' in beichi.get('type', ''):
            return {
                'type': '一卖',
                'price': bars['close'].iloc[-1],
                'reason': '上涨背驰终点',
                'confidence': 0.8
            }
        
        return None
    
    @staticmethod
    def second_sell(bars: pd.DataFrame, big_direction: str,
                    small_bi: Bi, prev_high: float) -> Optional[Dict]:
        """
        二卖: 反弹高点
        """
        if big_direction != '下跌':
            return None
        
        if small_bi and small_bi.direction == 'up':
            if small_bi.high <= prev_high * 1.01:  # 不过前高
                return {
                    'type': '二卖',
                    'price': bars['close'].iloc[-1],
                    'reason': '反弹不过前高',
                    'confidence': 0.7
                }
        
        return None
    
    @staticmethod
    def third_sell(bars: pd.DataFrame, zs: ZhongShu) -> Optional[Dict]:
        """
        三卖: 跌破中枢后反弹不过
        """
        if not zs:
            return None
        
        current_price = bars['close'].iloc[-1]
        
        # 跌破中枢
        if current_price < zs.low:
            # 反弹检查
            if current_price <= zs.low * 1.01:
                return {
                    'type': '三卖',
                    'price': current_price,
                    'reason': '跌破中枢后反弹不过',
                    'confidence': 0.75
                }
        
        return None
    
    @staticmethod
    def get_all_points(bars: pd.DataFrame, bi_list: List[Bi],
                       zs: ZhongShu, beichi: Dict,
                       big_direction: str) -> Dict:
        """
        获取所有买卖点
        
        Returns:
            {'buy': [一买、二买、三买], 'sell': [一卖、二卖、三卖]}
        """
        result = {
            'buy': [],
            'sell': []
        }
        
        # 买点
        first = BuySellPoints.first_buy(bars, bi_list, beichi)
        if first:
            result['buy'].append(first)
        
        if len(bi_list) >= 2:
            prev_low = bi_list[-2].low
            second = BuySellPoints.second_buy(bars, big_direction, bi_list[-1], prev_low)
            if second:
                result['buy'].append(second)
        
        third = BuySellPoints.third_buy(bars, zs)
        if third:
            result['buy'].append(third)
        
        # 卖点
        first_s = BuySellPoints.first_sell(bars, bi_list, beichi)
        if first_s:
            result['sell'].append(first_s)
        
        if len(bi_list) >= 2:
            prev_high = bi_list[-2].high
            second_s = BuySellPoints.second_sell(bars, big_direction, bi_list[-1], prev_high)
            if second_s:
                result['sell'].append(second_s)
        
        third_s = BuySellPoints.third_sell(bars, zs)
        if third_s:
            result['sell'].append(third_s)
        
        return result


# ==================== 增强版分析器 ====================

class EnhancedChanAnalyzer:
    """
    增强版缠论分析器
    
    整合: 中枢、笔、背驰、买卖点
    """
    
    def __init__(self, symbol: str, freqs: List[str] = None):
        self.symbol = symbol
        self.freqs = freqs or ['日线', '30分钟', '5分钟']
        self.data = {freq: None for freq in self.freqs}
        self.zhongshu = {freq: None for freq in self.freqs}
        self.bi = {freq: [] for freq in self.freqs}
        self.beichi = {freq: None for freq in self.freqs}
    
    def update(self, freq: str, bars: pd.DataFrame):
        """更新数据并计算"""
        self.data[freq] = bars
        
        # 识别中枢
        self.zhongshu[freq] = identify_zhongshu(bars)
        
        # 识别笔
        self.bi[freq] = identify_bi(bars)
        
        # 背驰检测
        if len(self.bi[freq]) >= 2:
            self.beichi[freq] = check_beichi(bars, self.bi[freq])
        else:
            self.beichi[freq] = None
        
        # 中枢背驰
        if self.zhongshu[freq]:
            zs_beichi = check_zhongshu_beichi(bars, self.zhongshu[freq])
            if zs_beichi:
                self.beichi[freq] = zs_beichi
    
    def get_direction(self, freq: str) -> str:
        """方向判断"""
        if freq not in self.data or self.data[freq] is None:
            return '未知'
        
        df = self.data[freq]
        if df['close'].iloc[-1] > df['open'].iloc[-1]:
            return '上涨'
        else:
            return '下跌'
    
    def get_analysis(self) -> Dict:
        """完整分析"""
        result = {}
        
        for freq in self.freqs:
            if self.data[freq] is None:
                continue
            
            # 买卖点
            big_dir = self.get_direction(freq)
            points = BuySellPoints.get_all_points(
                self.data[freq],
                self.bi[freq],
                self.zhongshu[freq],
                self.beichi[freq],
                big_dir
            )
            
            result[freq] = {
                'direction': big_dir,
                'zhongshu': str(self.zhongshu[freq]) if self.zhongshu[freq] else None,
                'beichi': self.beichi[freq],
                'bi_count': len(self.bi[freq]),
                'buy_points': points['buy'],
                'sell_points': points['sell']
            }
        
        return result


# ==================== 测试 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("增强版缠论分析测试")
    print("=" * 50)
    
    # 创建测试数据 - 模拟有中枢和背驰的走势
    np.random.seed(42)
    n = 100
    
    # 模拟先涨后跌再背驰
    prices = []
    base = 100
    # 上涨段
    prices.extend([base + i * 0.3 for i in range(20)])
    # 中枢区间
    prices.extend([106 + np.sin(i * 0.5) * 2 for i in range(20)])
    # 背驰段 - 涨幅明显减小
    prices.extend([106 + i * 0.1 for i in range(20)])
    # 下跌
    prices.extend([108 - i * 0.4 for i in range(20)])
    # 背驰后反弹
    prices.extend([100 + i * 0.2 for i in range(20)])
    
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=n),
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n)
    })
    
    # 测试中枢识别
    print("\n【中枢识别】")
    zs = identify_zhongshu(df)
    print(f"识别到: {zs}")
    
    # 测试笔识别
    print("\n【笔识别】")
    bits = identify_bi(df)
    print(f"识别到 {len(bits)} 笔")
    for b in bits[-3:]:
        print(f"  {b}")
    
    # 测试背驰检测
    print("\n【背驰检测】")
    beichi = check_beichi(df, bits)
    print(f"背驰: {beichi}")
    
    # 测试中枢背驰
    zs_beichi = check_zhongshu_beichi(df, zs)
    print(f"中枢背驰: {zs_beichi}")
    
    # 测试买卖点
    print("\n【买卖点】")
    direction = '上涨' if df['close'].iloc[-1] > df['open'].iloc[-1] else '下跌'
    points = BuySellPoints.get_all_points(df, bits, zs, beichi, direction)
    print(f"买点: {points['buy']}")
    print(f"卖点: {points['sell']}")
    
    # 完整分析
    print("\n【完整分析】")
    analyzer = EnhancedChanAnalyzer('000001', ['日线'])
    analyzer.update('日线', df)
    result = analyzer.get_analysis()
    print(result)
    
    print("\n✅ 增强版测试完成!")