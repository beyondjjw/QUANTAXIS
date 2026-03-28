# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略 - 完整版
包含: 月线牛熊判断、仓位控制、精确买卖点

作者: beyondjjw
版本: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict


# ==================== 级别配置 ====================

LEVELS = {
    '月线': {'freq': '1mon', 'role': '牛熊判断'},
    '周线': {'freq': '1week', 'role': '波段方向'},
    '日线': {'freq': 'D', 'role': '主操作周期'},
    '30分钟': {'freq': '30min', 'role': '精确买卖点'},
    '5分钟': {'freq': '5min', 'role': '仓位微调'},
}


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
        # 力度 = 幅度 * 成交量(如果有)
        self.force = abs(high - low) / low if low > 0 else 0
    
    def __repr__(self):
        return f"笔({'上涨' if self.direction == 'up' else '下跌'}, 高:{self.high:.2f}, 低:{self.low:.2f}, 力度:{self.force:.4f})"


def identify_bi(bars: pd.DataFrame) -> List[Bi]:
    """识别笔 - 简化版"""
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


# ==================== 中枢识别 ====================

class ZhongShu:
    """中枢"""
    def __init__(self, high: float, low: float, zg: float = None, zd: float = None):
        self.high = high
        self.low = low
        self.zg = zg or high  # 中枢上沿
        self.zd = zd or low   # 中枢下沿
        self.type = '上涨中枢' if high > low else '下跌中枢'
    
    def __repr__(self):
        return f"中枢(ZG:{self.zg:.2f}, ZD:{self.zd:.2f})"


def identify_zhongshu(bars: pd.DataFrame, min_bars: int = 5) -> Optional[ZhongShu]:
    """识别中枢 - 三段重叠区域"""
    if len(bars) < min_bars * 3:
        return None
    
    highs = bars['high'].values
    lows = bars['low'].values
    
    # 找重叠区域
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
    
    # 合并
    candidates.sort()
    merged = []
    for c in candidates:
        if not merged or c[0] > merged[-1][1]:
            merged.append(c)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]))
    
    if not merged:
        return None
    
    return ZhongShu(merged[0][1], merged[0][0], merged[0][1], merged[0][0])


# ==================== 背驰检测 ====================

def check_beichi(bi_list: List[Bi]) -> Optional[Dict]:
    """笔背驰检测"""
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
            'current_force': current.force,
            'prev_force': previous.force,
            'weaken': (previous.force - current.force) / previous.force
        }
    return None


def check_zhongshu_beichi(entry_change: float, exit_change: float, zs_type: str) -> Optional[Dict]:
    """中枢背驰检测"""
    if zs_type == '上涨中枢':
        if exit_change > 0 and exit_change < entry_change * 0.8:
            return {'type': '中枢背驰(上涨)', 'entry': entry_change, 'exit': exit_change}
    elif zs_type == '下跌中枢':
        if exit_change < 0 and abs(exit_change) < abs(entry_change) * 0.8:
            return {'type': '中枢背驰(下跌)', 'entry': entry_change, 'exit': exit_change}
    return None


# ==================== 多级别分析器 ====================

class MultiLevelChanAnalyzer:
    """多级别缠论分析器"""
    
    def __init__(self, symbol: str, freqs: List[str] = None):
        self.symbol = symbol
        self.freqs = freqs or ['月线', '日线', '30分钟']
        self.data = {freq: None for freq in self.freqs}
        self.bi = {freq: [] for freq in self.freqs}
        self.zhongshu = {freq: None for freq in self.freqs}
        self.beichi = {freq: None for freq in self.freqs}
    
    def update(self, freq: str, bars: pd.DataFrame):
        """更新数据"""
        self.data[freq] = bars
        
        if bars is not None and len(bars) >= 5:
            self.bi[freq] = identify_bi(bars)
            self.zhongshu[freq] = identify_zhongshu(bars)
            
            if len(self.bi[freq]) >= 2:
                self.beichi[freq] = check_beichi(self.bi[freq])
    
    def get_month_direction(self) -> str:
        """月线牛熊判断"""
        if '月线' not in self.data or self.data['月线'] is None:
            return '未知'
        
        df = self.data['月线']
        if len(df) < 60:
            return '未知'
        
        ma12 = df['close'].rolling(12).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]
        
        return '牛市' if ma12 > ma60 else '熊市'
    
    def get_direction(self, freq: str) -> str:
        """方向判断"""
        if freq not in self.data or self.data[freq] is None:
            return '未知'
        
        df = self.data[freq]
        if df['close'].iloc[-1] > df['open'].iloc[-1]:
            return '上涨'
        return '下跌'
    
    def get_trend(self, freq: str) -> str:
        """趋势判断"""
        if freq not in self.data or self.data[freq] is None:
            return '未知'
        
        df = self.data[freq]
        if len(df) < 60:
            return '构建中'
        
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]
        
        if ma20 > ma60:
            return '上涨趋势'
        elif ma20 < ma60:
            return '下跌趋势'
        return '盘整'
    
    def get_buy_point(self, freq: str) -> Dict:
        """获取买卖点"""
        result = {'buy': [], 'sell': []}
        
        if freq not in self.data or self.data[freq] is None:
            return result
        
        direction = self.get_direction(freq)
        bi_list = self.bi[freq]
        zs = self.zhongshu[freq]
        beichi = self.beichi[freq]
        
        # 一买: 下跌背驰终点
        if beichi and '下跌' in str(beichi.get('type', '')):
            result['buy'].append({'type': '一买', 'confidence': 0.7})
        
        # 二买: 上涨中回调不破前低
        if direction == '上涨' and len(bi_list) >= 2:
            if bi_list[-1].direction == 'down' and bi_list[-1].low >= bi_list[-2].low * 0.99:
                result['buy'].append({'type': '二买', 'confidence': 0.8})
        
        # 三买: 突破中枢后回调不破ZG
        if zs and direction == '上涨':
            current_price = self.data[freq]['close'].iloc[-1]
            if current_price > zs.zg:
                if current_price >= zs.zg * 0.99:
                    result['buy'].append({'type': '三买', 'confidence': 0.75})
        
        # 一卖: 上涨背驰
        if beichi and '上涨' in str(beichi.get('type', '')):
            result['sell'].append({'type': '一卖', 'confidence': 0.8})
        
        # 二卖: 下跌中反弹不过前高
        if direction == '下跌' and len(bi_list) >= 2:
            if bi_list[-1].direction == 'up' and bi_list[-1].high <= bi_list[-2].high * 1.01:
                result['sell'].append({'type': '二卖', 'confidence': 0.7})
        
        # 三卖: 跌破中枢后反弹不过ZD
        if zs and direction == '下跌':
            current_price = self.data[freq]['close'].iloc[-1]
            if current_price < zs.zd:
                if current_price <= zs.zd * 1.01:
                    result['sell'].append({'type': '三卖', 'confidence': 0.75})
        
        return result
    
    def get_analysis(self) -> Dict:
        """完整分析"""
        result = {
            'month_direction': self.get_month_direction(),
            'levels': {}
        }
        
        for freq in self.freqs:
            buy_point = self.get_buy_point(freq)
            result['levels'][freq] = {
                'direction': self.get_direction(freq),
                'trend': self.get_trend(freq),
                'beichi': self.beichi[freq],
                'zhongshu': str(self.zhongshu[freq]) if self.zhongshu[freq] else None,
                'bi_count': len(self.bi[freq]),
                'buy_points': buy_point['buy'],
                'sell_points': buy_point['sell']
            }
        
        return result


# ==================== 完整策略 ====================

class ChanMultiLevelStrategy:
    """
    缠论多级别联立完整策略
    
    包含:
    - 月线牛熊判断
    - 仓位控制
    - 精确买卖点
    """
    
    def __init__(self, 
                 max_position: float = 0.8,
                 stop_loss: float = 0.05,
                 profit_target: float = 0.30):
        self.max_position = max_position
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        
        # 持仓
        self.position = 0
        self.entry_price = 0
        self.entry_time = None
        
        # 信号记录
        self.signals = []
    
    def get_position_limit(self, month_direction: str) -> float:
        """根据月线牛熊调整仓位"""
        if month_direction == '牛市':
            return 0.8
        elif month_direction == '熊市':
            return 0.0  # 熊市不开新仓
        return 0.5  # 震荡市半仓
    
    def analyze(self, analyzer: MultiLevelChanAnalyzer) -> Dict:
        """分析并生成信号"""
        analysis = analyzer.get_analysis()
        month_dir = analysis.get('month_direction', '未知')
        
        # 仓位限制
        position_limit = self.get_position_limit(month_dir)
        
        if position_limit == 0:
            return {
                'action': 'watch',
                'reason': f'月线{month_dir}，不开新仓',
                'position_limit': position_limit,
                'analysis': analysis
            }
        
        # 日线分析
        daily = analysis.get('levels', {}).get('日线', {})
        if not daily:
            return {'action': 'hold', 'reason': '日线数据不足', 'position_limit': position_limit}
        
        # 30分钟分析
        min30 = analysis.get('levels', {}).get('30分钟', {})
        
        action = 'hold'
        reason = ''
        confidence = 0.5
        position = position_limit
        
        daily_dir = daily.get('direction', '未知')
        daily_beichi = daily.get('beichi')
        
        # 买点检测
        buy_points = daily.get('buy_points', [])
        if buy_points:
            # 优先二买/三买
            for bp in buy_points:
                if bp['type'] in ['二买', '三买'] and self.position == 0:
                    action = 'buy'
                    reason = f"日线{bp['type']}, 月线{month_dir}"
                    confidence = bp['confidence']
                    position = 0.5 if bp['type'] == '二买' else 0.3
                    break
        
        # 卖点检测
        if action == 'hold':
            sell_points = daily.get('sell_points', [])
            if sell_points and self.position > 0:
                for sp in sell_points:
                    if sp['type'] in ['一卖', '二卖']:
                        action = 'sell'
                        reason = f"日线{sp['type']}"
                        confidence = sp['confidence']
                        break
        
        # 大级别背驰
        if action == 'hold' and daily_beichi:
            if '上涨' in str(daily_beichi.get('type', '')) and self.position > 0:
                action = 'sell'
                reason = f"日线背驰见顶"
                confidence = 0.8
        
        # 记录信号
        signal = {
            'action': action,
            'reason': reason,
            'confidence': confidence,
            'position_limit': position_limit,
            'month_direction': month_dir,
            'analysis': analysis
        }
        self.signals.append(signal)
        
        return signal
    
    def execute(self, signal: Dict, current_price: float) -> Dict:
        """执行信号"""
        action = signal.get('action', 'hold')
        position_limit = signal.get('position_limit', 0.8)
        
        result = {
            'action': 'none',
            'price': current_price,
            'volume': 0,
            'reason': signal.get('reason', '')
        }
        
        if action == 'buy' and self.position == 0:
            volume = position_limit / current_price
            self.position = volume
            self.entry_price = current_price
            result['action'] = 'buy'
            result['volume'] = volume
            result['position'] = position_limit
        
        elif action == 'sell' and self.position > 0:
            result['action'] = 'sell'
            result['volume'] = self.position
            self.position = 0
            self.entry_price = 0
        
        return result
    
    def check_stop_loss(self, current_price: float) -> bool:
        """止损检查"""
        if self.position == 0:
            return False
        return (current_price - self.entry_price) / self.entry_price < -self.stop_loss
    
    def check_take_profit(self, current_price: float) -> bool:
        """止盈检查"""
        if self.position == 0:
            return False
        return (current_price - self.entry_price) / self.entry_price > self.profit_target


# ==================== 测试 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("完整版缠论多级别联立策略测试")
    print("=" * 50)
    
    # 创建模拟数据
    np.random.seed(42)
    n = 200
    
    # 月线数据
    dates = pd.date_range('2020-01-01', periods=n, freq='M')
    month_data = pd.DataFrame({
        'date': dates,
        'open': 100 + np.random.randn(n).cumsum(),
        'high': 105 + np.random.randn(n).cumsum(),
        'low': 95 + np.random.randn(n).cumsum(),
        'close': 100 + np.random.randn(n).cumsum(),
        'volume': np.random.randint(1000000, 10000000, n)
    })
    
    # 日线数据
    dates = pd.date_range('2024-01-01', periods=100)
    daily_data = pd.DataFrame({
        'date': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 103,
        'low': np.random.randn(100).cumsum() + 97,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # 30分钟数据
    min30_data = daily_data.copy()
    
    # 创建分析器
    analyzer = MultiLevelChanAnalyzer('000001', ['月线', '日线', '30分钟'])
    analyzer.update('月线', month_data)
    analyzer.update('日线', daily_data)
    analyzer.update('30分钟', min30_data)
    
    # 分析
    print("\n【月线牛熊判断】")
    print(f"月线方向: {analyzer.get_month_direction()}")
    
    print("\n【日线分析】")
    analysis = analyzer.get_analysis()
    daily = analysis['levels']['日线']
    print(f"方向: {daily['direction']}")
    print(f"趋势: {daily['trend']}")
    print(f"背驰: {daily['beichi']}")
    print(f"中枢: {daily['zhongshu']}")
    print(f"买点: {daily['buy_points']}")
    print(f"卖点: {daily['sell_points']}")
    
    # 策略测试
    print("\n【策略信号】")
    strategy = ChanMultiLevelStrategy()
    signal = strategy.analyze(analyzer)
    print(f"动作: {signal['action']}")
    print(f"原因: {signal['reason']}")
    print(f"仓位限制: {signal['position_limit']}")
    print(f"月线方向: {signal['month_direction']}")
    
    # 执行
    result = strategy.execute(signal, 100.0)
    print(f"\n执行结果: {result}")
    
    print("\n✅ 完整版测试完成!")