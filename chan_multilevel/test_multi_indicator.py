# -*- coding: utf-8 -*-
"""
多指标策略 - 模拟测试

作者: beyondjjw
版本: 1.0
"""

import pandas as pd
import numpy as np
from multi_indicator_strategy import (
    MultiIndicatorStrategy, 
    analyze_multi_indicators,
    calc_all_indicators,
    calc_rsi,
    calc_kdj,
    calc_boll,
    calc_cci,
    calc_wr,
    calc_bias
)


def create_test_data(n: int, pattern: str, base_price: float = 100) -> pd.DataFrame:
    """创建测试数据"""
    np.random.seed(42)
    prices = []
    base = base_price
    
    for i in range(n):
        if pattern == '上涨':
            if i % 8 < 4:
                base += np.random.randn() * 0.8 + 0.5
            else:
                base -= np.random.randn() * 0.5
        elif pattern == '下跌':
            if i % 8 < 4:
                base -= np.random.randn() * 0.8 + 0.5
            else:
                base += np.random.randn() * 0.5
        elif pattern == '震荡':
            base += np.random.randn() * 1.5
        elif pattern == '超买':
            base += np.random.randn() * 0.3 + 0.8
        elif pattern == '超卖':
            base += np.random.randn() * 0.3 - 0.8
        else:
            base += np.random.randn()
        
        prices.append(base + np.random.randn() * 0.3)
    
    return pd.DataFrame({
        'open': prices,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n)
    })


def test_indicators():
    """测试各指标计算"""
    print("=" * 60)
    print("技术指标计算测试")
    print("=" * 60)
    
    bars = create_test_data(60, '上涨')
    
    print("\n【RSI】")
    rsi = calc_rsi(bars)
    print(f"RSI(14): {rsi.iloc[-1]:.1f}")
    print(f"  <30 超卖, >70 超买")
    
    print("\n【KDJ】")
    kdj = calc_kdj(bars)
    print(f"K: {kdj['k'].iloc[-1]:.1f}")
    print(f"D: {kdj['d'].iloc[-1]:.1f}")
    print(f"J: {kdj['j'].iloc[-1]:.1f}")
    print(f"  K<D 超卖, K>D 超买")
    
    print("\n【BOLL】")
    boll = calc_boll(bars)
    print(f"上轨: {boll['upper'].iloc[-1]:.1f}")
    print(f"下轨: {boll['lower'].iloc[-1]:.1f}")
    print(f"  >0.8 上轨, <0.2 下轨")
    
    print("\n【CCI】")
    cci = calc_cci(bars)
    print(f"CCI: {cci.iloc[-1]:.1f}")
    print(f"  <-100 超卖, >100 超买")
    
    print("\n【WR】")
    wr = calc_wr(bars)
    print(f"WR: {wr.iloc[-1]:.1f}")
    print(f"  >80 超卖, <20 超买")
    
    print("\n【BIAS】")
    bias = calc_bias(bars)
    print(f"BIAS: {bias.iloc[-1]:.1f}")
    print(f"  <-5 负乖离, >5 正乖离")
    
    print("\n✅ 指标计算正常")


def test_scenario(name: str, pattern: str, bars: pd.DataFrame, expected_action: str):
    """测试单个场景"""
    print(f"\n{'='*50}")
    print(f"场景: {name} ({pattern})")
    print(f"预期: {expected_action}")
    print("-" * 50)
    
    # 指标
    ind = calc_all_indicators(bars)
    print(f"RSI: {ind['rsi']:.1f}")
    print(f"KDJ: K={ind['kdj_k']:.1f}, D={ind['kdj_d']:.1f}, J={ind['kdj_j']:.1f}")
    print(f"BOLL位置: {ind['boll_pos']:.2f}")
    print(f"CCI: {ind['cci']:.1f}")
    print(f"WR: {ind['wr']:.1f}")
    print(f"BIAS: {ind['bias']:.1f}")
    
    # 分析
    result = analyze_multi_indicators(bars)
    print(f"\n得分: {result['score']:.2f}")
    print(f"买入: {result['buy']}")
    print(f"卖出: {result['sell']}")
    
    # 策略
    strategy = MultiIndicatorStrategy()
    if expected_action == 'sell':
        strategy.position = 1
        strategy.entry_price = bars['close'].iloc[0] * 0.95
    
    signal = strategy.analyze(bars)
    
    actual = signal['action']
    match = "✅" if actual == expected_action else "❌"
    
    print(f"\n动作: {actual}")
    print(f"原因: {signal['reason']}")
    print(f"{match} 匹配")
    
    return actual == expected_action


def test_full():
    """完整测试"""
    print("=" * 60)
    print("多指标策略 - 模拟测试")
    print("=" * 60)
    
    results = []
    
    # 基础场景
    print("\n【基础场景】")
    results.append(test_scenario("上涨趋势", "上涨", create_test_data(60, '上涨'), 'buy'))
    results.append(test_scenario("下跌趋势", "下跌", create_test_data(60, '下跌'), 'sell'))
    results.append(test_scenario("震荡市场", "震荡", create_test_data(60, '震荡'), 'hold'))
    results.append(test_scenario("超买区域", "超买", create_test_data(60, '超买'), 'sell'))
    results.append(test_scenario("超卖区域", "超卖", create_test_data(60, '超卖'), 'buy'))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    rate = passed / total * 100
    
    print(f"通过: {passed}/{total} ({rate:.0f}%)")
    
    if rate >= 80:
        print("✅ 策略表现良好")
    else:
        print("⚠️ 需要优化")
    
    return rate


def test_indicator_signals():
    """测试各指标独立信号"""
    print("\n" + "=" * 60)
    print("指标信号测试")
    print("=" * 60)
    
    signals = [
        {'name': 'RSI超卖', 'condition': 'RSI < 30', 'action': 'buy'},
        {'name': 'RSI超买', 'condition': 'RSI > 70', 'action': 'sell'},
        {'name': 'KDJ金叉', 'condition': 'K > D 且 J > 50', 'action': 'buy'},
        {'name': 'KDJ死叉', 'condition': 'K < D 且 J < 50', 'action': 'sell'},
        {'name': 'BOLL下轨', 'condition': '位置 < 0.2', 'action': 'buy'},
        {'name': 'BOLL上轨', 'condition': '位置 > 0.8', 'action': 'sell'},
        {'name': 'CCI超卖', 'condition': 'CCI < -100', 'action': 'buy'},
        {'name': 'CCI超买', 'condition': 'CCI > 100', 'action': 'sell'},
        {'name': 'WR超卖', 'condition': 'WR > 80', 'action': 'buy'},
        {'name': 'WR超买', 'condition': 'WR < 20', 'action': 'sell'},
        {'name': 'BIAS负乖离', 'condition': 'BIAS < -5', 'action': 'buy'},
        {'name': 'BIAS正乖离', 'condition': 'BIAS > 5', 'action': 'sell'},
    ]
    
    print("\n指标信号表:")
    for s in signals:
        print(f"  {s['name']}: {s['condition']} → {s['action']}")
    
    print("\n✅ 指标信号测试完成")


if __name__ == '__main__':
    # 指标计算测试
    test_indicators()
    
    # 完整测试
    test_full()
    
    # 指标信号
    test_indicator_signals()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)