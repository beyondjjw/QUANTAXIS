# 缠论多级别联立分析策略

## 目录
1. [理论基础](#1-理论基础)
2. [级别联立逻辑](#2-级别联立逻辑)
3. [信号系统](#3-信号系统)
4. [策略实现](#4-策略实现)
5. [完整代码](#5-完整代码)

---

## 1. 理论基础

### 1.1 缠论核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                       缠论分析层次                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  K线 → 分型 → 笔 → 线段 → 中枢 → 趋势 → 背驰                    │
│   ↓     ↓     ↓     ↓      ↓      ↓      ↓                     │
│  最小  顶/底  连接  走势  震荡   方向  力度                      │
│  单位  形态  成笔  段    区间   切换  衰竭                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 多级别联立原理

| 级别 | 周期 | 作用 |
|-----|------|------|
| **月线** | 1Month | 定方向 (牛市/熊市) |
| **周线** | 1Week | 定波段 (上涨/下跌/盘整) |
| **日线** | 1Day | 主操作周期 |
| **30分** | 30min | 买卖点精确 |
| **5分** | 5min | 进出点位 |

### 1.3 核心原则

> **大级别看方向，小级别找买点**
> - 大级别上涨 → 小级别回调结束买入
> - 大级别下跌 → 小级别反弹结束卖出
> - 大级别盘整 → 区间震荡高抛低吸

---

## 2. 级别联立逻辑

### 2.1 联立判断表

```
┌────────────────────────────────────────────────────────────────────┐
│                      多级别联立判断                                 │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│   大级别      │   小级别      │    操作      │      说明         │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│   上涨       │   回调整理    │    买       │ 大级别向上，小级别 │
│              │   (背驰)     │             │ 回调出现背驰      │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│   上涨       │   继续上涨   │   持股/加仓  │ 顺势而为          │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│   下跌       │   反弹结束   │   卖        │ 大级别向下，小级别 │
│              │   (背驰)     │             │ 反弹出现背驰      │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│   下跌       │   继续下跌   │   持币/观望  │ 下降趋势          │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│   盘整       │   突破       │   跟进      │ 区间突破          │
├──────────────┼──────────────┼──────────────┼───────────────────┤
│   盘整       │   背驰       │   反向      │ 假突破            │
└──────────────┴──────────────┴──────────────┴───────────────────┘
```

### 2.2 买卖点级别

```
┌─────────────────────────────────────────────────────────────────┐
│                      缠论买卖点                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  一买 (一买)                                                    │
│  ├── 大级别一买: 日线/周线下跌背驰                            │
│  └── 小级别一买: 30分/5分下跌背驰                            │
│       ↓                                                         │
│  二买 (二买)                                                    │
│  ├── 大级别二买: 周线/日线回调不破新低                       │
│  └── 小级别二买: 30分/5分回调不破一买                         │
│       ↓                                                         │
│  三买 (三买)                                                    │
│  ├── 大级别三买: 日线突破中枢后回调不破                       │
│  └── 小级别三买: 30分突破中枢后回调不破                       │
│       ↓                                                         │
│  一卖/二卖/三卖 (同理)                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 信号系统

### 3.1 笔信号 (bxt)

```python
# 笔系统信号
from czsc.signals.bxt import *

# 主要信号
Signal_BI_Close_High    # 向上笔创新高
Signal_BI_Close_Low    # 向下笔创新低
Signal_BI_Power_Max    # 笔力度最大
Signal_BI_BiZheng      # 笔背驰
```

### 3.2 中枢信号

```python
# 中枢相关
from czsc.analyze import ZS

# 信号
ZS_形成       # 中枢形成
ZS_破坏       # 中枢破坏 (三买卖点)
ZS_扩张       # 中枢扩张
ZS_新生       # 中枢新生
```

### 3.3 背驰信号

```python
# 背驰判断
from czsc.signals import bi_bei_chi

# 背驰类型
bei_chi_zs   # 中枢背驰
bei_chi_bi   # 笔背驰
bei_chi_dd   # 段背驰
```

---

## 4. 策略实现

### 4.1 多级别分析器

```python
class MultiLevelChan:
    """多级别缠论分析器"""
    
    def __init__(self, symbol, freqs=['日线', '30分钟', '5分钟']):
        self.symbol = symbol
        self.freqs = freqs
        self.kas = {}  # 不同级别的K线分析器
        
        # 初始化各周期
        for freq in freqs:
            self.kas[freq] = KlineAnalyze(freq)
    
    def update(self, bar):
        """更新数据"""
        for freq in self.freqs:
            self.kas[freq].update(bar)
    
    def get_direction(self, freq):
        """获取级别方向"""
        kas = self.kas[freq]
        
        if len(kas.bis) < 2:
            return 'unknown'
        
        # 最近两笔方向
        last_bi = kas.bis[-1]
        prev_bi = kas.bis[-2]
        
        if last_bi.direction == Direction.Up:
            return '上涨'
        else:
            return '下跌'
    
    def get_trend(self, freq):
        """获取趋势状态"""
        kas = self.kas[freq]
        
        # 有无中枢
        if len(kas.zhongduans) > 0:
            return '盘整'
        
        # 有几笔
        if len(kas.bis) >= 5:
            return '趋势'
        
        return '构建中'
    
    def check_beichi(self, freq):
        """检查背驰"""
        kas = self.kas[freq]
        
        if len(kas.bis) < 3:
            return None
        
        # 比较最近两笔力度
        bi1 = kas.bis[-2]
        bi2 = kas.bis[-1]
        
        # 计算笔高/笔低
        high1 = max(bi1.high, bi1.low) if bi1.direction == Direction.Up else bi1.high
        high2 = max(bi2.high, bi2.low) if bi2.direction == Direction.Up else bi2.high
        
        low1 = bi1.low if bi1.direction == Direction.Up else min(bi1.high, bi1.low)
        low2 = bi2.low if bi2.direction == Direction.Up else min(bi2.high, bi2.low)
        
        power1 = high1 - low1
        power2 = high2 - low2
        
        if bi2.direction == Direction.Up:
            # 向上比较上涨力度
            if power2 < power1:
                return '上涨背驰'
        else:
            # 向下比较下跌力度
            if power2 < power1:
                return '下跌背驰'
        
        return None
```

### 4.2 多级别联立策略

```python
class MultiLevelStrategy(QAStockStrategy):
    """多级别联立策略"""
    
    name = 'MultiLevelChan'
    
    def init(self):
        # 级别配置
        self.levels = {
            '日线': {'freq': 'D', 'role': '方向'},
            '30分钟': {'freq': '30min', 'role': '操作'},
            '5分钟': {'freq': '5min', 'role': '精确'},
        }
        
        # 创建多级别分析器
        self.analyzer = MultiLevelChan(self.symbol, list(self.levels.keys()))
        
        # 状态
        self.position_opened = False
        self.entry_price = 0
        self.entry_time = None
    
    def on_bar(self, bar):
        """每个K线回调"""
        # 更新分析器
        self.analyzer.update(bar)
        
        # 获取各级别状态
        daily_direction = self.analyzer.get_direction('日线')
        min30_direction = self.analyzer.get_direction('30分钟')
        
        # 大级别判断
        if daily_direction == '上涨':
            # 大级别向上
            self.handle_uptrend(bar)
        elif daily_direction == '下跌':
            # 大级别向下
            self.handle_downtrend(bar)
        else:
            # 未知，保持观望
    
    def handle_uptrend(self, bar):
        """处理上涨趋势"""
        # 检查小级别是否出现回调结束信号
        min30_trend = self.analyzer.get_trend('30分钟')
        min30_beichi = self.analyzer.check_beichi('30分钟')
        
        if not self.position_opened:
            # 无持仓，寻找买点
            if min30_beichi == '下跌背驰':
                # 小级别下跌背驰，可能是一买/二买
                self.buy(
                    code=bar.code,
                    price=bar.close,
                    volume=self.params.get('position_size', 0.3)
                )
                self.position_opened = True
                self.entry_price = bar.close
                self.entry_time = bar.dt
                
        else:
            # 有持仓，检查卖点
            # 大级别出现卖点
            if self.check_big_sell():
                self.sell_all()
                self.position_opened = False
    
    def handle_downtrend(self, handle):
        """处理下跌趋势"""
        # 持币观望，或做空（如果支持）
        if self.position_opened:
            # 止损
            loss = (bar.close - self.entry_price) / self.entry_price
            if loss < -self.params.get('stop_loss', 0.05):
                self.sell_all()
                self.position_opened = False
    
    def check_big_sell(self):
        """检查大级别卖点"""
        # 日线出现顶分型或背驰
        daily_beichi = self.analyzer.check_beichi('日线')
        
        if daily_beichi in ['上涨背驰']:
            return True
        
        # 或30分钟出现卖点
        min30_beichi = self.analyzer.check_beichi('30分钟')
        if min30_beichi in ['上涨背驰'] and self.has_profit(0.1):
            return True
        
        return False
    
    def has_profit(self, threshold):
        """检查是否有盈利"""
        if not self.position_opened:
            return False
        current = self.current_price()
        profit = (current - self.entry_price) / self.entry_price
        return profit > threshold
```

### 4.3 完整交易信号

```python
class ChanTradingSignals:
    """缠论交易信号生成器"""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.kas = {}  # 多级别K线分析器
    
    def update(self, data_dict):
        """
        data_dict: {freq: dataframe}
        """
        for freq, df in data_dict.items():
            if freq not in self.kas:
                self.kas[freq] = KlineAnalyze(df)
            else:
                self.kas[freq].update(df)
    
    def get_signals(self, levels=['日线', '30分钟']):
        """
        生成多级别联立信号
        
        返回: {
            'big_level': {...},    # 大级别信号
            'mid_level': {...},   # 中级别信号  
            'small_level': {...}, # 小级别信号
            'action': 'buy/sell/hold',  # 操作建议
            'confidence': 0-1,     # 置信度
            'reason': '原因说明'
        }
        """
        signals = {}
        
        # 分析每个级别
        for level in levels:
            if level not in self.kas:
                continue
            
            kas = self.kas[level]
            signals[level] = self.analyze_level(kas)
        
        # 联立判断
        result = self.combine_signals(signals)
        
        return result
    
    def analyze_level(self, kas):
        """分析单个级别"""
        s = {
            'direction': 'unknown',
            'trend': 'unknown',
            'has_beichi': False,
            'has_zs': False,
            'last_bi_power': 0,
        }
        
        if len(kas.bis) < 2:
            return s
        
        # 方向
        last_bi = kas.bis[-1]
        s['direction'] = '上涨' if last_bi.direction == Direction.Up else '下跌'
        
        # 趋势
        if len(kas.zhongduans) > 0:
            s['trend'] = '盘整'
        elif len(kas.bis) >= 5:
            s['trend'] = '趋势'
        else:
            s['trend'] = '构建中'
        
        # 背驰
        if len(kas.bis) >= 3:
            s['has_beichi'] = self.check_beichi(kas)
        
        # 中枢
        s['has_zs'] = len(kas.zhongduans) > 0
        
        # 笔力度
        if len(kas.bis) >= 2:
            bi = kas.bis[-1]
            s['last_bi_power'] = abs(bi.high - bi.low)
        
        return s
    
    def check_beichi(self, kas):
        """检查背驰"""
        if len(kas.bis) < 3:
            return False
        
        bi1 = kas.bis[-2]
        bi2 = kas.bis[-1]
        
        power1 = abs(bi1.high - bi1.low)
        power2 = abs(bi2.high - bi2.low)
        
        if bi2.direction == Direction.Up:
            return power2 < power1  # 上涨背驰
        else:
            return power2 < power1  # 下跌背驰
    
    def combine_signals(self, signals):
        """联立多级别信号"""
        if len(signals) < 2:
            return {'action': 'hold', 'reason': '数据不足'}
        
        # 取大级别(第一个)和次级别
        levels = list(signals.keys())
        big = signals[levels[0]]
        small = signals[levels[1]]
        
        action = 'hold'
        reason = ''
        confidence = 0.5
        
        # 上涨趋势联立
        if big['direction'] == '上涨':
            if not small['has_beichi']:
                # 小级别无背驰，继续持有
                action = 'hold'
                reason = '大级别上涨，小级别无背驰'
                confidence = 0.7
            else:
                # 小级别背驰，可能是一买
                action = 'buy'
                reason = '大级别上涨，小级别背驰，可能是一买'
                confidence = 0.8
        
        # 下跌趋势联立
        elif big['direction'] == '下跌':
            if not small['has_beichi']:
                action = 'hold'
                reason = '大级别下跌，小级别无背驰'
                confidence = 0.7
            else:
                action = 'sell'
                reason = '大级别下跌，小级别背驰，可能是卖点'
                confidence = 0.8
        
        # 盘整
        elif big['trend'] == '盘整':
            if big['has_zs'] and small['direction'] == '下跌':
                action = 'buy'
                reason = '大级别盘整中枢下轨，小级别下跌，三买机会'
                confidence = 0.6
        
        return {
            'big_level': big,
            'small_level': small,
            'action': action,
            'reason': reason,
            'confidence': confidence
        }
```

---

## 5. 完整代码

### 5.1 多级别联立策略完整实现

```python
# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略

大级别上涨盘整趋势 → 小级别买点进 → 大级别卖点出
"""

from QUANTAXIS.QAStrategy import QAStockStrategy
from czsc import KlineAnalyze
from czsc.enum import Direction


class ChanMultiLevelStrategy(QAStockStrategy):
    """缠论多级别联立策略"""
    
    name = 'ChanMultiLevel'
    
    def init(self):
        """初始化"""
        # 级别配置 (从大到小)
        self.levels = [
            {'name': '日线', 'freq': 'D', 'role': '方向'},
            {'name': '30分钟', 'freq': '30min', 'role': '操作'},
            {'name': '5分钟', 'freq': '5min', 'role': '精确'},
        ]
        
        # 各周期K线分析器
        self.kas = {level['name']: KlineAnalyze(freq=level['freq']) 
                    for level in self.levels}
        
        # 交易参数
        self.params = {
            'max_position': 0.8,      # 最大仓位
            'stop_loss': 0.05,        # 止损线
            'profit_target': 0.20,     # 止盈线
            'min_confidence': 0.6,   # 最小置信度
        }
        
        # 持仓状态
        self.has_position = False
        self.entry_price = 0
        self.entry_time = None
        
        print(f"策略初始化: {self.name}")
    
    def on_bar(self, bar):
        """K线回调"""
        # 更新各周期数据
        for level in self.levels:
            freq = level['freq']
            # 实际使用时需要按频率聚合数据
            # self.kas[level['name']].update(bar)
        
        # 生成信号
        signals = self.generate_signals()
        
        # 执行交易
        self.execute_signals(signals, bar)
    
    def generate_signals(self):
        """生成多级别联立信号"""
        signals = {}
        
        # 分析每个级别
        for level in self.levels:
            name = level['name']
            kas = self.kas[name]
            
            signals[name] = self.analyze_single_level(kas)
        
        # 联立判断
        combined = self.combine_levels(signals)
        
        return combined
    
    def analyze_single_level(self, kas):
        """分析单个级别"""
        s = {
            'direction': 'unknown',
            'trend': 'unknown',
            'beichi': False,
            'has_zs': False,
            'power': 0,
        }
        
        if not kas.bis or len(kas.bis) < 2:
            return s
        
        # 方向
        s['direction'] = '上涨' if kas.bis[-1].direction == Direction.Up else '下跌'
        
        # 趋势
        s['trend'] = '盘整' if kas.zhongduans else ('趋势' if len(kas.bis) >= 5 else '构建')
        
        # 背驰
        if len(kas.bis) >= 3:
            s['beichi'] = self.check_beichi(kas)
        
        # 中枢
        s['has_zs'] = bool(kas.zhongduans)
        
        # 力度
        if kas.bis:
            last_bi = kas.bis[-1]
            s['power'] = abs(last_bi.high - last_bi.low)
        
        return s
    
    def check_beichi(self, kas):
        """背驰判断"""
        if len(kas.bis) < 3:
            return False
        
        bi1 = kas.bis[-2]
        bi2 = kas.bis[-1]
        
        power1 = abs(bi1.high - bi1.low)
        power2 = abs(bi2.high - bi2.low)
        
        # 力度减小 = 背驰
        return power2 < power1
    
    def combine_levels(self, signals):
        """多级别联立"""
        if len(signals) < 2:
            return {'action': 'hold', 'confidence': 0}
        
        # 日线 = 大级别, 30分钟 = 小级别
        big = signals.get('日线', {})
        small = signals.get('30分钟', {})
        
        action = 'hold'
        reason = ''
        confidence = 0.5
        
        # ===== 大级别上涨 =====
        if big.get('direction') == '上涨':
            if big.get('beichi'):
                # 大级别背驰，可能转折
                action = 'sell' if self.has_position else 'watch'
                reason = '大级别背驰，可能见顶'
                confidence = 0.8
            elif small.get('beichi'):
                # 小级别背驰，大级别未背 -> 可能是二买/三买
                action = 'buy' if not self.has_position else 'hold'
                reason = '小级别背驰，大级别上涨延续，二买'
                confidence = 0.7
            else:
                # 都无背驰，持有
                action = 'hold' if self.has_position else 'buy'
                reason = '上涨延续，无背驰信号'
                confidence = 0.6
        
        # ===== 大级别下跌 =====
        elif big.get('direction') == '下跌':
            if small.get('beichi'):
                # 小级别背驰，可能是反弹终点
                action = 'sell' if self.has_position else 'watch'
                reason = '小级别背驰，反弹结束'
                confidence = 0.7
            else:
                action = 'watch'
                reason = '下跌趋势，观望'
                confidence = 0.8
        
        # ===== 大级别盘整 =====
        elif big.get('trend') == '盘整':
            if not small.get('has_zs') and small.get('direction') == '下跌':
                # 突破后回调不破 -> 三买
                action = 'buy' if not self.has_position else 'hold'
                reason = '盘整突破三买'
                confidence = 0.7
        
        # 仓位检查
        current_position = self.get_position_ratio()
        if action == 'buy' and current_position >= self.params['max_position']:
            action = 'hold'
            reason += ' (仓位已满)'
        
        # 止损止盈
        if self.has_position:
            profit = (self.current_price() - self.entry_price) / self.entry_price
            
            # 止损
            if profit < -self.params['stop_loss']:
                action = 'sell'
                reason = f'止损 {profit:.1%}'
                confidence = 0.9
            
            # 止盈
            elif profit > self.params['profit_target']:
                action = 'sell'
                reason = f'止盈 {profit:.1%}'
                confidence = 0.8
        
        return {
            'action': action,
            'reason': reason,
            'confidence': confidence,
            'signals': signals
        }
    
    def execute_signals(self, signals, bar):
        """执行信号"""
        action = signals.get('action', 'hold')
        
        if action == 'buy' and not self.has_position:
            volume = self.params['max_position']
            self.buy(code=bar.code, price=bar.close, volume=volume)
            self.has_position = True
            self.entry_price = bar.close
            self.entry_time = bar.dt
            print(f"买入: {bar.code} @ {bar.close}, 原因: {signals.get('reason')}")
        
        elif action == 'sell' and self.has_position:
            self.sell(code=bar.code, price=bar.close, volume='all')
            self.has_position = False
            print(f"卖出: {bar.code} @ {bar.close}, 原因: {signals.get('reason')}")
        
        # 记录信号
        if action != 'hold':
            self.log(f"信号: {action}, 置信度: {signals.get('confidence'):.2f}, 原因: {signals.get('reason')}")
    
    def get_position_ratio(self):
        """获取持仓比例"""
        if not self.has_position:
            return 0
        
        position_value = self.positions_value
        total_value = self.account.total_value
        
        return position_value / total_value if total_value > 0 else 0
    
    def current_price(self):
        """获取当前价"""
        # 实际实现需要从市场获取实时价格
        return self.last_price


# ==================== 使用示例 ====================

if __name__ == '__main__':
    # 策略配置
    config = {
        'strategy': ChanMultiLevelStrategy,
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'initial_cash': 1000000,
        'commission': 0.0003,
    }
    
    # 运行回测
    from QUANTAXIS.QAStrategy import QABacktest
    
    bt = QABacktest(**config)
    result = bt.run()
    
    # 查看结果
    print(f"年化收益: {result.annual_return():.2%}")
    print(f"夏普比率: {result.sharpe_ratio():.2f}")
    print(f"最大回撤: {result.max_drawdown():.2%}")
```

### 5.2 因子+缠论增强

```python
class ChanFactorStrategy(QAStockStrategy):
    """因子+缠论增强策略"""
    
    def init(self):
        # 因子配置
        self.factors = ['macd', 'rsi', 'volume']
        
        # 缠论配置
        self.chan_levels = ['日线', '30分钟']
        
        # 综合评分权重
        self.weights = {
            'factor': 0.4,    # 因子得分
            'chan': 0.6,      # 缠论信号
        }
    
    def on_bar(self, bar):
        # 1. 因子选股
        factor_score = self.calc_factor_score(bar.code)
        
        # 2. 缠论信号
        chan_signal = self.get_chan_signal(bar.code)
        
        # 3. 综合评分
        total_score = (
            factor_score * self.weights['factor'] +
            chan_signal * self.weights['chan']
        )
        
        # 4. 交易执行
        if total_score > 0.8 and not self.has_position:
            self.buy(bar.code, bar.close, 0.3)
        elif total_score < 0.3 and self.has_position:
            self.sell_all()
    
    def calc_factor_score(self, code):
        """计算因子得分"""
        # 获取因子值
        macd = self.get_factor('macd', code)
        rsi = self.get_factor('rsi', code)
        vol = self.get_factor('volume', code)
        
        # 评分
        score = 0
        if macd > 0:
            score += 0.3
        if rsi < 30 or rsi > 70:
            score += 0.2
        if vol > 1.5:  # 放量
            score += 0.2
        
        return score
    
    def get_chan_signal(self, code):
        """获取缠论信号得分"""
        # 简化的缠论信号
        # 实际需要完整的ChanTradingSignals类
        
        direction = self.get_direction(code, '30分钟')
        beichi = self.check_beichi(code, '30分钟')
        
        score = 0.5  # 基础分
        
        if direction == '上涨':
            score += 0.3
        if beichi:
            score += 0.2
        
        return score
```

---

## 总结

### 策略核心逻辑

```
┌─────────────────────────────────────────────────────────────────┐
│                   多级别联立策略核心                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  大级别(方向) ──▶ 中级别(波段) ──▶ 小级别(精确)                │
│      ↓                ↓                 ↓                       │
│  日线/周线        30分钟            5分钟                      │
│      │                │                 │                       │
│      ├─ 上涨 ────────┼─ 回调结束 ─────┼─ 背驰 → 买入          │
│      │                │                 │                       │
│      ├─ 上涨 ────────┼─ 无背驰 ───────┼─ 继续持有             │
│      │                │                 │                       │
│      ├─ 下跌 ────────┼─ 反弹结束 ─────┼─ 背驰 → 卖出          │
│      │                │                 │                       │
│      └─ 盘整 ────────┼─ 突破 ─────────┼─ 回调不破 → 三买      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 关键点

1. **大级别定方向** - 日线/周线判断牛熊
2. **小级别找买点** - 30分/5分精确入场
3. **背驰是关键** - 力度衰竭是转折信号
4. **三买/三卖** - 中枢突破后的机会

---

*文档版本: 1.0*
*更新时间: 2026-03-28*
*作者: beyondjjw*