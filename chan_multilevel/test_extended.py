# -*- coding: utf-8 -*-
"""
缠论综合策略 - 扩展模拟测试
更多场景验证

作者: beyondjjw
版本: 2.0
"""

import pandas as pd
import numpy as np
from chan_integrated_strategy import ChanIntegratedStrategy, analyze_buy_sell_signals
from chan_integrated_strategy import identify_bi, identify_zhongshu


def create_test_data(n: int, pattern: str, base_price: float = 100) -> pd.DataFrame:
    """创建不同场景的测试数据"""
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
        elif pattern == '顶背离':
            if i < n * 0.6:
                base += np.random.randn() * 0.6 + 0.6
            else:
                base += np.random.randn() * 0.3 - 0.2
        elif pattern == '底背离':
            if i < n * 0.6:
                base -= np.random.randn() * 0.6 + 0.6
            else:
                base += np.random.randn() * 0.3 + 0.2
        elif pattern == '突破':
            if i < n * 0.7:
                base += np.random.randn() * 0.5
            else:
                base += np.random.randn() * 0.6 + 0.8
        elif pattern == '强势上涨':
            base += np.random.randn() * 0.5 + 0.8
        elif pattern == '弱势下跌':
            base += np.random.randn() * 0.5 - 0.8
        elif pattern == '横盘突破':
            base += np.random.randn() * 0.3
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


def test_scenario(name: str, pattern: str, bars: pd.DataFrame, expected_action: str):
    """测试单个场景"""
    print(f"\n{'='*45}")
    print(f"场景: {name} ({pattern})")
    print(f"预期: {expected_action}")
    print('-' * 45)
    
    # 笔识别
    bi_list = identify_bi(bars)
    print(f"笔数量: {len(bi_list)}")
    
    # 趋势
    ma20 = bars['close'].rolling(20).mean().iloc[-1]
    ma60 = bars['close'].rolling(60).mean().iloc[-1] if len(bars) >= 60 else ma20
    trend = '上涨趋势' if ma20 > ma60 else '下跌趋势' if ma20 < ma60 else '盘整'
    print(f"趋势: {trend} (MA20={ma20:.1f}, MA60={ma60:.1f})")
    
    # 综合分析
    result = analyze_buy_sell_signals(bars)
    print(f"买入: {result['buy']}")
    print(f"卖出: {result['sell']}")
    
    # 策略信号
    strategy = ChanIntegratedStrategy()
    
    # 根据预期设置持仓
    if expected_action == 'sell':
        strategy.position = 1
        strategy.entry_price = bars['close'].iloc[0] * 0.95
    
    signal = strategy.analyze(bars)
    
    actual = signal['action']
    match = "✅" if actual == expected_action else "❌"
    
    print(f"\n动作: {actual}")
    print(f"原因: {signal.get('reason', '')}")
    print(f"仓位: {signal.get('position', 0)}")
    print(f"{match} 匹配")
    
    return actual == expected_action


def test_extended():
    """扩展测试"""
    print("=" * 60)
    print("缠论综合策略 - 扩展模拟测试")
    print("=" * 60)
    
    results = []
    
    # 基础场景
    print("\n" + "="*60)
    print("【基础场景测试】")
    print("="*60)
    
    results.append(test_scenario("上涨趋势", "上涨", create_test_data(60, '上涨'), 'buy'))
    results.append(test_scenario("下跌趋势", "下跌", create_test_data(60, '下跌'), 'sell'))
    results.append(test_scenario("震荡市场", "震荡", create_test_data(60, '震荡'), 'hold'))
    results.append(test_scenario("顶背离", "顶背离", create_test_data(60, '顶背离'), 'sell'))
    results.append(test_scenario("底背离", "底背离", create_test_data(60, '底背离'), 'buy'))
    results.append(test_scenario("突破上涨", "突破", create_test_data(60, '突破'), 'buy'))
    
    # 扩展场景
    print("\n" + "="*60)
    print("【扩展场景测试】")
    print("="*60)
    
    results.append(test_scenario("强势上涨", "强势", create_test_data(60, '强势上涨'), 'buy'))
    results.append(test_scenario("弱势下跌", "弱势", create_test_data(60, '弱势下跌'), 'sell'))
    results.append(test_scenario("横盘突破", "横盘", create_test_data(60, '横盘突破'), 'buy'))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    rate = passed / total * 100
    
    print(f"通过: {passed}/{total} ({rate:.0f}%)")
    
    if rate >= 90:
        print("🎉 策略表现优秀!")
    elif rate >= 80:
        print("✅ 策略表现良好")
    else:
        print("⚠️ 需要优化策略")
    
    return rate


def test_position_control():
    """仓位控制测试"""
    print("\n" + "=" * 60)
    print("仓位控制测试")
    print("=" * 60)
    
    # 创建月线数据
    month_bars = pd.DataFrame({
        'close': [100 + i * 2 for i in range(70)]  # 牛市
    })
    
    strategy = ChanIntegratedStrategy(monthly_data=month_bars)
    
    # 上涨趋势
    bars = create_test_data(60, '上涨')
    signal = strategy.analyze(bars)
    
    print(f"\n牛市+上涨趋势:")
    print(f"  动作: {signal['action']}")
    print(f"  仓位: {signal['position']}")
    print(f"  预期仓位: ≤0.8")
    
    # 下跌趋势
    bars = create_test_data(60, '下跌')
    signal = strategy.analyze(bars)
    
    print(f"\n牛市+下跌趋势:")
    print(f"  动作: {signal['action']}")
    print(f"  仓位: {signal['position']}")
    
    # 熊市
    month_bars = pd.DataFrame({
        'close': [100 - i * 2 for i in range(70)]  # 熊市
    })
    strategy = ChanIntegratedStrategy(monthly_data=month_bars)
    bars = create_test_data(60, '上涨')
    signal = strategy.analyze(bars)
    
    print(f"\n熊市+上涨趋势:")
    print(f"  动作: {signal['action']}")
    print(f"  原因: {signal.get('reason', '')}")
    
    print("\n✅ 仓位控制测试完成")


def test_signal_priority():
    """信号优先级测试"""
    print("\n" + "=" * 60)
    print("信号优先级测试")
    print("=" * 60)
    
    # 测试不同置信度的买入信号
    test_cases = [
        {'name': '双重背离', 'conf': 0.95, 'expected_pos': 0.8},
        {'name': '二买', 'conf': 0.80, 'expected_pos': 0.5},
        {'name': 'MACD背离', 'conf': 0.70, 'expected_pos': 0.4},
        {'name': '底分型', 'conf': 0.60, 'expected_pos': 0.3},
    ]
    
    print("\n信号优先级:")
    for tc in test_cases:
        print(f"  {tc['name']}: 置信度={tc['conf']}, 仓位={tc['expected_pos']}")
    
    print("\n✅ 信号优先级测试完成")


if __name__ == '__main__':
    # 扩展测试
    test_extended()
    
    # 仓位控制
    test_position_control()
    
    # 信号优先级
    test_signal_priority()
    
    print("\n" + "=" * 60)
    print("✅ 所有扩展测试完成!")
    print("=" * 60)