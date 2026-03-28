# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略 - 多种数据测试
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/ws/plan/chan_multilevel')

from chan_multilevel_strategy import (
    MultiLevelChanAnalyzer,
    ChanMultiLevelStrategy,
    ChanFactorStrategy,
)


def create_uptrend_data(n=100, start_price=100):
    """上涨趋势数据"""
    dates = pd.date_range('2024-01-01', periods=n)
    trend = np.linspace(0, 20, n)
    noise = np.random.randn(n) * 2
    prices = start_price + trend + noise
    
    return pd.DataFrame({
        'date': dates,
        'open': prices - np.random.rand(n) * 0.5,
        'high': prices + np.random.rand(n) * 0.5,
        'low': prices - np.random.rand(n) * 0.5,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n),
    })


def create_downtrend_data(n=100, start_price=150):
    """下跌趋势数据"""
    dates = pd.date_range('2024-01-01', periods=n)
    trend = np.linspace(0, -20, n)
    noise = np.random.randn(n) * 2
    prices = start_price + trend + noise
    
    return pd.DataFrame({
        'date': dates,
        'open': prices + np.random.rand(n) * 0.5,
        'high': prices + np.random.rand(n) * 0.5,
        'low': prices - np.random.rand(n) * 0.5,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n),
    })


def create_sideway_data(n=100, start_price=100):
    """震荡/盘整数据"""
    dates = pd.date_range('2024-01-01', periods=n)
    # 震荡行情
    t = np.linspace(0, 4 * np.pi, n)
    prices = start_price + np.sin(t) * 10 + np.random.randn(n) * 2
    
    return pd.DataFrame({
        'date': dates,
        'open': prices - np.random.rand(n) * 0.5,
        'high': prices + np.random.rand(n) * 0.5,
        'low': prices - np.random.rand(n) * 0.5,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n),
    })


def create_volatile_data(n=100, start_price=100):
    """剧烈波动数据"""
    dates = pd.date_range('2024-01-01', periods=n)
    # 大幅波动
    prices = start_price + np.cumsum(np.random.randn(n) * 3)
    
    return pd.DataFrame({
        'date': dates,
        'open': prices - np.random.rand(n) * 2,
        'high': prices + np.random.rand(n) * 2,
        'low': prices - np.random.rand(n) * 2,
        'close': prices,
        'volume': np.random.randint(5000000, 20000000, n),
    })


def test_data_type(name, data, expected_direction=None):
    """测试单种数据类型"""
    print(f"\n{'='*40}")
    print(f"测试: {name}")
    print(f"{'='*40}")
    
    # 创建分析器
    analyzer = MultiLevelChanAnalyzer('000001', ['日线', '30分钟', '5分钟'])
    analyzer.update('日线', data)
    
    # 获取分析结果
    direction = analyzer.get_direction('日线')
    trend = analyzer.get_trend('日线')
    
    print(f"方向: {direction}")
    print(f"趋势: {trend}")
    
    # 测试策略
    strategy = ChanMultiLevelStrategy()
    signal = strategy.analyze(analyzer)
    print(f"信号: {signal['action']} (置信度: {signal['confidence']})")
    print(f"原因: {signal['reason']}")
    
    # 测试因子策略
    factor_strategy = ChanFactorStrategy()
    factor_signal = factor_strategy.generate_signal(data, analyzer)
    print(f"因子信号: {factor_signal['action']} (得分: {factor_signal['score']:.2f})")
    
    # 验证
    if expected_direction and direction != expected_direction:
        print(f"⚠️ 方向预期 {expected_direction}, 实际 {direction}")
    
    return {
        'direction': direction,
        'trend': trend,
        'signal': signal['action'],
        'factor_signal': factor_signal['action'],
    }


def main():
    print("\n" + "="*50)
    print("多种数据测试")
    print("="*50)
    
    results = []
    
    # 1. 上涨趋势
    np.random.seed(42)
    data1 = create_uptrend_data(100, 100)
    r1 = test_data_type("上涨趋势", data1, "上涨")
    results.append(("上涨趋势", r1))
    
    # 2. 下跌趋势
    np.random.seed(43)
    data2 = create_downtrend_data(100, 150)
    r2 = test_data_type("下跌趋势", data2, "下跌")
    results.append(("下跌趋势", r2))
    
    # 3. 震荡盘整
    np.random.seed(44)
    data3 = create_sideway_data(100, 100)
    r3 = test_data_type("震荡盘整", data3)
    results.append(("震荡盘整", r3))
    
    # 4. 剧烈波动
    np.random.seed(45)
    data4 = create_volatile_data(100, 100)
    r4 = test_data_type("剧烈波动", data4)
    results.append(("剧烈波动", r4))
    
    # 5. 不同价格区间
    print("\n" + "="*50)
    print("价格区间测试")
    print("="*50)
    
    for price in [10, 50, 100, 500, 1000]:
        np.random.seed(42)
        data = create_uptrend_data(50, price)
        analyzer = MultiLevelChanAnalyzer('000001', ['日线'])
        analyzer.update('日线', data)
        direction = analyzer.get_direction('日线')
        print(f"价格 {price}: 方向 {direction}")
    
    # 总结
    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    for name, r in results:
        print(f"{name}: 方向={r['direction']}, 信号={r['signal']}")
    
    print("\n✅ 多种数据测试完成!")


if __name__ == '__main__':
    main()