# -*- coding: utf-8 -*-
"""
缠论多级别联立分析策略测试
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, '/ws/plan/chan_multilevel')

from chan_multilevel_strategy import (
    MultiLevelChanAnalyzer,
    ChanMultiLevelStrategy,
    ChanFactorStrategy,
    create_multi_analyzer,
    run_strategy
)


def create_test_data(n=100, start_price=100):
    """创建测试数据"""
    dates = pd.date_range('2024-01-01', periods=n)
    
    # 生成带趋势的数据
    np.random.seed(42)
    trend = np.linspace(0, 10, n)  # 上涨趋势
    noise = np.random.randn(n) * 2
    
    prices = start_price + trend + noise
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices - np.random.rand(n) * 0.5,
        'high': prices + np.random.rand(n) * 0.5,
        'low': prices - np.random.rand(n) * 0.5,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n),
    })
    
    # 添加技术指标
    # MACD
    data['ma12'] = data['close'].rolling(12).mean()
    data['ma26'] = data['close'].rolling(26).mean()
    data['macd'] = data['ma12'] - data['ma26']
    
    # RSI
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    return data


def test_multi_level_analyzer():
    """测试多级别分析器"""
    print("=" * 50)
    print("测试: MultiLevelChanAnalyzer")
    print("=" * 50)
    
    # 创建分析器
    analyzer = MultiLevelChanAnalyzer('000001', ['日线', '30分钟', '5分钟'])
    
    # 更新日线数据
    data = create_test_data(100)
    analyzer.update('日线', data)
    
    # 测试方法
    direction = analyzer.get_direction('日线')
    print(f"日线方向: {direction}")
    
    trend = analyzer.get_trend('日线')
    print(f"日线趋势: {trend}")
    
    beichi = analyzer.get_trend('日线')
    print(f"日线背驰检测: {beichi}")
    
    # 获取完整分析
    analysis = analyzer.get_analysis()
    print(f"完整分析: {analysis}")
    
    print("✓ MultiLevelChanAnalyzer 测试通过\n")


def test_strategy():
    """测试策略"""
    print("=" * 50)
    print("测试: ChanMultiLevelStrategy")
    print("=" * 50)
    
    # 创建分析器
    analyzer = MultiLevelChanAnalyzer('000001', ['日线', '30分钟', '5分钟'])
    data = create_test_data(100)
    analyzer.update('日线', data)
    
    # 创建策略
    strategy = ChanMultiLevelStrategy(
        max_position=0.8,
        stop_loss=0.05,
        profit_target=0.20
    )
    
    # 分析
    signal = strategy.analyze(analyzer)
    print(f"信号: {signal['action']}")
    print(f"原因: {signal['reason']}")
    print(f"置信度: {signal['confidence']}")
    
    # 执行
    result = strategy.execute(signal, 110.0)
    print(f"执行: {result}")
    
    print("✓ ChanMultiLevelStrategy 测试通过\n")


def test_factor_strategy():
    """测试因子增强策略"""
    print("=" * 50)
    print("测试: ChanFactorStrategy")
    print("=" * 50)
    
    # 创建测试数据
    data = create_test_data(100)
    
    # 创建分析器
    analyzer = MultiLevelChanAnalyzer('000001', ['日线', '30分钟', '5分钟'])
    analyzer.update('日线', data)
    
    # 创建策略
    strategy = ChanFactorStrategy()
    
    # 生成信号
    signal = strategy.generate_signal(data, analyzer)
    print(f"信号: {signal['action']}")
    print(f"综合得分: {signal['score']:.3f}")
    print(f"因子得分: {signal['factor_score']:.3f}")
    print(f"缠论得分: {signal['chan_score']:.3f}")
    print(f"原因: {signal['reason']}")
    
    print("✓ ChanFactorStrategy 测试通过\n")


def test_full_workflow():
    """测试完整工作流"""
    print("=" * 50)
    print("测试: 完整工作流")
    print("=" * 50)
    
    # 准备数据
    data_dict = {
        '日线': create_test_data(200),
        '30分钟': create_test_data(800),
        '5分钟': create_test_data(4800),
    }
    
    # 创建分析器
    analyzer = create_multi_analyzer('000001', data_dict)
    
    # 运行策略
    result = run_strategy(data_dict['日线'], analyzer)
    
    print(f"信号: {result['signal']['action']}")
    print(f"结果: {result['result']}")
    
    print("✓ 完整工作流测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("缠论多级别联立分析策略 - 测试")
    print("=" * 50 + "\n")
    
    try:
        test_multi_level_analyzer()
        test_strategy()
        test_factor_strategy()
        test_full_workflow()
        
        print("=" * 50)
        print("✓ 所有测试通过!")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()