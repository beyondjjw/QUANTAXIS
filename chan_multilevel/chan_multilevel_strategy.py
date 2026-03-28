# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略实现
基于 czsc_multilevel_strategy.md 文档

作者: beyondjjw
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict


class MultiLevelChanAnalyzer:
    """
    多级别缠论分析器
    
    用途: 
    - 多周期K线数据管理
    - 级别方向判断
    - 背驰检测
    - 中枢识别
    """
    
    # 级别配置
    LEVELS = {
        '年线': {'freq': '12mon', 'role': '长期'},
        '季线': {'freq': '季线', 'role': '中期'},
        '月线': {'freq': '1mon', 'role': '方向'},
        '周线': {'freq': '1week', 'role': '波段'},
        '日线': {'freq': 'D', 'role': '主操作'},
        '30分钟': {'freq': '30min', 'role': '操作'},
        '5分钟': {'freq': '5min', 'role': '精确'},
        '1分钟': {'freq': '1min', 'role': '点位'},
    }
    
    def __init__(self, symbol: str, freqs: List[str] = None):
        """
        初始化
        
        Args:
            symbol: 股票代码
            freqs: 关注的周期列表
        """
        self.symbol = symbol
        self.freqs = freqs or ['日线', '30分钟', '5分钟']
        self.data = {freq: [] for freq in self.freqs}
        self.kas = {}  # 各周期K线分析器
        
    def update(self, freq: str, bars: pd.DataFrame):
        """
        更新周期数据
        
        Args:
            freq: 周期名称
            bars: K线数据 DataFrame
        """
        if freq in self.data:
            self.data[freq] = bars
    
    def get_direction(self, freq: str) -> str:
        """
        获取周期方向
        
        Args:
            freq: 周期名称
            
        Returns:
            '上涨' / '下跌' / '未知'
        """
        if freq not in self.data or len(self.data[freq]) < 2:
            return '未知'
        
        df = self.data[freq]
        # 简化的方向判断
        if df['close'].iloc[-1] > df['open'].iloc[-1]:
            return '上涨'
        else:
            return '下跌'
    
    def get_trend(self, freq: str) -> str:
        """
        获取趋势状态
        
        Args:
            freq: 周期名称
            
        Returns:
            '上涨趋势' / '下跌趋势' / '盘整' / '构建中'
        """
        if freq not in self.data:
            return '未知'
        
        df = self.data[freq]
        if len(df) < 20:
            return '构建中'
        
        # 简化判断
        ma20 = df['close'].rolling(20).mean()
        ma60 = df['close'].rolling(60).mean()
        
        if ma20.iloc[-1] > ma60.iloc[-1]:
            return '上涨趋势'
        elif ma20.iloc[-1] < ma60.iloc[-1]:
            return '下跌趋势'
        else:
            return '盘整'
    
    def check_beichi(self, freq: str, n: int = 2) -> Optional[str]:
        """
        检查背驰
        
        Args:
            freq: 周期名称
            n: 比较的笔数
            
        Returns:
            '上涨背驰' / '下跌背驰' / None
        """
        if freq not in self.data:
            return None
        
        df = self.data[freq]
        if len(df) < n + 1:
            return None
        
        # 计算最近n个周期的涨跌幅
        changes = df['close'].pct_change().tail(n)
        
        if len(changes) < 2:
            return None
        
        # 比较力度
        if changes.iloc[-1] < changes.iloc[-2]:
            if changes.iloc[-1] > 0:
                return '上涨背驰'
            else:
                return '下跌背驰'
        
        return None
    
    def get_analysis(self) -> Dict:
        """
        获取多级别分析结果
        
        Returns:
            分析结果字典
        """
        result = {}
        
        for freq in self.freqs:
            result[freq] = {
                'direction': self.get_direction(freq),
                'trend': self.get_trend(freq),
                'beichi': self.check_beichi(freq),
            }
        
        return result


class ChanMultiLevelStrategy:
    """
    缠论多级别联立策略
    
    核心逻辑:
    - 大级别上涨 → 小级别回调结束买入
    - 大级别下跌 → 小级别反弹结束卖出
    - 大级别盘整 → 突破后回调不破买入
    """
    
    def __init__(self, 
                 max_position: float = 0.8,
                 stop_loss: float = 0.05,
                 profit_target: float = 0.20):
        """
        初始化策略
        
        Args:
            max_position: 最大仓位比例
            stop_loss: 止损比例
            profit_target: 止盈比例
        """
        self.max_position = max_position
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        
        # 持仓状态
        self.position = 0  # 持仓数量
        self.entry_price = 0  # 持仓成本
        self.entry_time = None  # 持仓时间
        
        # 信号记录
        self.signals = []
    
    def analyze(self, analyzer: MultiLevelChanAnalyzer) -> Dict:
        """
        分析并生成信号
        
        Args:
            analyzer: 多级别分析器
            
        Returns:
            交易信号字典
        """
        analysis = analyzer.get_analysis()
        
        if len(analysis) < 2:
            return {'action': 'hold', 'reason': '数据不足'}
        
        # 大级别 = 第一个, 小级别 = 第二个
        levels = list(analysis.keys())
        big = analysis[levels[0]]
        small = analysis[levels[1]]
        
        action = 'hold'
        reason = ''
        confidence = 0.5
        
        # ===== 大级别上涨 =====
        if big['direction'] == '上涨':
            if big.get('beichi'):
                # 大级别背驰，可能见顶
                action = 'sell' if self.position > 0 else 'watch'
                reason = '大级别背驰，可能见顶'
                confidence = 0.8
            elif small.get('beichi'):
                # 小级别背驰，大级别未背 -> 可能是二买/三买
                action = 'buy' if self.position == 0 else 'hold'
                reason = '小级别背驰，大级别上涨延续，二买'
                confidence = 0.7
            else:
                # 都无背驰，持有或买入
                action = 'hold' if self.position > 0 else 'buy'
                reason = '上涨延续，无背驰信号'
                confidence = 0.6
        
        # ===== 大级别下跌 =====
        elif big['direction'] == '下跌':
            if small.get('beichi'):
                # 小级别背驰，可能是反弹终点
                action = 'sell' if self.position > 0 else 'watch'
                reason = '小级别背驰，反弹结束'
                confidence = 0.7
            else:
                action = 'watch'
                reason = '下跌趋势，观望'
                confidence = 0.8
        
        # ===== 大级别盘整 =====
        elif big['trend'] == '盘整':
            if not small.get('beichi') and small['direction'] == '下跌':
                action = 'buy' if self.position == 0 else 'hold'
                reason = '盘整突破三买机会'
                confidence = 0.7
        
        # 止损止盈检查
        if self.position > 0:
            # 假设当前价格需要从外部传入
            # profit = (current_price - self.entry_price) / self.entry_price
            pass
        
        # 记录信号
        signal = {
            'action': action,
            'reason': reason,
            'confidence': confidence,
            'analysis': analysis
        }
        self.signals.append(signal)
        
        return signal
    
    def execute(self, signal: Dict, current_price: float, current_time=None) -> Dict:
        """
        执行信号
        
        Args:
            signal: 交易信号
            current_price: 当前价格
            current_time: 当前时间
            
        Returns:
            执行结果
        """
        action = signal.get('action', 'hold')
        
        result = {
            'action': 'none',
            'price': current_price,
            'volume': 0,
            'reason': signal.get('reason', '')
        }
        
        if action == 'buy' and self.position == 0:
            volume = self.max_position / current_price
            self.position = volume
            self.entry_price = current_price
            self.entry_time = current_time
            
            result['action'] = 'buy'
            result['volume'] = volume
            
        elif action == 'sell' and self.position > 0:
            result['action'] = 'sell'
            result['volume'] = self.position
            
            self.position = 0
            self.entry_price = 0
            self.entry_time = None
        
        return result
    
    def check_stop_loss(self, current_price: float) -> bool:
        """
        检查是否触发止损
        
        Args:
            current_price: 当前价格
            
        Returns:
            是否触发止损
        """
        if self.position == 0 or self.entry_price == 0:
            return False
        
        loss = (current_price - self.entry_price) / self.entry_price
        
        if loss < -self.stop_loss:
            return True
        
        return False
    
    def check_take_profit(self, current_price: float) -> bool:
        """
        检查是否触发止盈
        
        Args:
            current_price: 当前价格
            
        Returns:
            是否触发止盈
        """
        if self.position == 0 or self.entry_price == 0:
            return False
        
        profit = (current_price - self.entry_price) / self.entry_price
        
        if profit > self.profit_target:
            return True
        
        return False


class ChanFactorStrategy:
    """
    因子+缠论增强策略
    
    综合因子得分和缠论信号进行决策
    """
    
    def __init__(self):
        # 权重配置
        self.factor_weight = 0.4
        self.chan_weight = 0.6
        
        # 持仓
        self.position = 0
        self.entry_price = 0
    
    def calc_factor_score(self, data: pd.DataFrame) -> float:
        """
        计算因子得分
        
        Args:
            data: 股票数据
            
        Returns:
            因子得分 0-1
        """
        score = 0.5
        
        # MACD
        if 'macd' in data.columns:
            if data['macd'].iloc[-1] > 0:
                score += 0.2
        
        # RSI
        if 'rsi' in data.columns:
            rsi = data['rsi'].iloc[-1]
            if rsi < 30 or rsi > 70:
                score += 0.15
        
        # 成交量
        if 'volume' in data.columns:
            vol_ma5 = data['volume'].rolling(5).mean().iloc[-1]
            vol_ma20 = data['volume'].rolling(20).mean().iloc[-1]
            if vol_ma5 > vol_ma20 * 1.5:
                score += 0.15
        
        return min(score, 1.0)
    
    def calc_chan_score(self, analyzer: MultiLevelChanAnalyzer) -> float:
        """
        计算缠论信号得分
        
        Args:
            analyzer: 多级别分析器
            
        Returns:
            缠论得分 0-1
        """
        analysis = analyzer.get_analysis()
        
        # 简化的缠论评分
        score = 0.5
        
        if '日线' in analysis:
            daily = analysis['日线']
            
            if daily['direction'] == '上涨':
                score += 0.2
            
            if daily.get('beichi') and '背驰' in str(daily['beichi']):
                score -= 0.1  # 背驰可能见顶
        
        if '30分钟' in analysis:
            min30 = analysis['30分钟']
            
            if min30.get('beichi') and '背驰' in str(min30['beichi']):
                score += 0.3  # 小级别背驰可能是买点
        
        return min(max(score, 0), 1.0)
    
    def generate_signal(self, data: pd.DataFrame, analyzer: MultiLevelChanAnalyzer) -> Dict:
        """
        生成综合信号
        
        Args:
            data: 股票数据
            analyzer: 多级别分析器
            
        Returns:
            交易信号
        """
        # 因子得分
        factor_score = self.calc_factor_score(data)
        
        # 缠论得分
        chan_score = self.calc_chan_score(analyzer)
        
        # 综合得分
        total_score = (
            factor_score * self.factor_weight +
            chan_score * self.chan_weight
        )
        
        # 生成信号
        if total_score > 0.75 and self.position == 0:
            action = 'buy'
            reason = f'因子:{factor_score:.2f}, 缠论:{chan_score:.2f}, 综合:{total_score:.2f}'
        elif total_score < 0.35 and self.position > 0:
            action = 'sell'
            reason = f'综合得分过低 {total_score:.2f}'
        else:
            action = 'hold'
            reason = f'综合得分 {total_score:.2f}'
        
        return {
            'action': action,
            'score': total_score,
            'factor_score': factor_score,
            'chan_score': chan_score,
            'reason': reason
        }


# ==================== 辅助函数 ====================

def create_multi_analyzer(symbol: str, data_dict: Dict[str, pd.DataFrame]) -> MultiLevelChanAnalyzer:
    """
    创建多级别分析器
    
    Args:
        symbol: 股票代码
        data_dict: {周期: DataFrame}
        
    Returns:
        MultiLevelChanAnalyzer 实例
    """
    analyzer = MultiLevelChanAnalyzer(symbol)
    
    for freq, df in data_dict.items():
        if freq in analyzer.data:
            analyzer.update(freq, df)
    
    return analyzer


def run_strategy(data: pd.DataFrame, analyzer: MultiLevelChanAnalyzer) -> Dict:
    """
    运行策略
    
    Args:
        data: 股票数据
        analyzer: 多级别分析器
        
    Returns:
        策略结果
    """
    strategy = ChanMultiLevelStrategy()
    
    # 分析
    signal = strategy.analyze(analyzer)
    
    # 假设当前价格
    current_price = data['close'].iloc[-1]
    
    # 执行
    result = strategy.execute(signal, current_price)
    
    return {
        'signal': signal,
        'result': result
    }


# ==================== 测试 ====================

if __name__ == '__main__':
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100)
    test_data = pd.DataFrame({
        'date': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 103,
        'low': np.random.randn(100).cumsum() + 97,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # 创建分析器
    analyzer = MultiLevelChanAnalyzer('000001', ['日线', '30分钟', '5分钟'])
    analyzer.update('日线', test_data)
    
    # 策略测试
    strategy = ChanMultiLevelStrategy()
    signal = strategy.analyze(analyzer)
    
    print("多级别分析:", analyzer.get_analysis())
    print("交易信号:", signal)
    
    # 执行
    result = strategy.execute(signal, 100.0)
    print("执行结果:", result)