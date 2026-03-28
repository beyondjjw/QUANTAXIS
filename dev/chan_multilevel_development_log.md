# 缠论多级别联立量化交易策略 - 开发日志

**作者**: beyondjjw  
**日期**: 2026-03-28  
**版本**: 1.0

---

## 一、项目概述

本项目实现了基于缠论的多级别联立量化交易策略，整合了多种技术指标（RSI/KDJ/BOLL/CCI/WR/BIAS/MACD），支持日线级别和30分钟级别的趋势分析和交易信号。

### 1.1 核心理念

> **大级别定方向，小级别找精确买点**

- 大周期决定战略（做多/做空/观望）
- 小周期决定战术（何时买、何时卖）
- 多指标验证提高准确率

### 1.2 策略类型

| 策略 | 级别 | 适用场景 |
|------|------|----------|
| 日线中长线 | 日线为主 | 趋势波段 |
| 30分钟短线 | 30分钟 | 波段交易 |
| 多指标综合 | 多级别+多指标 | 精细化交易 |

---

## 二、目录结构

```
/ws/QUANTAXIS/chan_multilevel/
├── 文档
│   ├── SPEC.md                      # 基础规范文档
│   ├── chan_multilevel_thought.md   # 缠论多级别联立思想
│   ├── li_xiaojun_strategy.md       # 李晓军实盘策略
│   ├── strategy_30min_short.md      # 30分钟短线策略
│   └── chan_macd_divergence.md      # 缠论+MACD背离
│
├── 策略代码
│   ├── chan_multilevel_strategy.py  # 基础版策略
│   ├── chan_full_strategy.py       # 完整版策略(月线牛熊)
│   ├── chan_enhanced.py            # 增强功能(中枢/背驰/买卖点)
│   ├── chan_integrated_strategy.py  # 综合策略(买入/卖出/仓位)
│   ├── strategy_30min.py            # 30分钟短线策略
│   ├── chan_macd_strategy.py        # MACD背离策略
│   └── multi_indicator_strategy.py # 多指标综合策略
│
└── 测试代码
    ├── test_strategy.py             # 基础测试
    ├── test_enhanced.py             # 增强功能测试
    ├── test_multi_data.py           # 多种数据测试
    ├── test_simulate.py             # 综合策略模拟
    ├── test_extended.py             # 扩展场景测试
    └── test_multi_indicator.py      # 多指标测试
```

---

## 三、功能实现

### 3.1 缠论基础功能

| 功能 | 实现文件 | 说明 |
|------|----------|------|
| 笔识别 | `identify_bi()` | 顶底分型识别 |
| 中枢识别 | `identify_zhongshu()` | 三段重叠区域 |
| 背驰检测 | `check_beichi()` | 笔力度对比 |
| 买卖点 | BuySellPoints类 | 一买~三买/一卖~三卖 |

### 3.2 多级别联立

| 级别 | 周期 | 作用 |
|------|------|------|
| 月线 | 1mon | 牛熊判断(MA12>MA60) |
| 周线 | 1week | 波段方向 |
| 日线 | D | 主操作周期 |
| 30分钟 | 30min | 精确买卖点 |
| 5分钟 | 5min | 仓位微调 |

### 3.3 技术指标

| 指标 | 计算函数 | 买入条件 | 卖出条件 |
|------|----------|----------|----------|
| RSI | calc_rsi() | RSI < 30 | RSI > 70 |
| KDJ | calc_kdj() | 金叉/超卖 | 死叉/超买 |
| BOLL | calc_boll() | 位置 < 0.2 | 位置 > 0.8 |
| CCI | calc_cci() | CCI < -100 | CCI > 100 |
| WR | calc_wr() | WR > 80 | WR < 20 |
| BIAS | calc_bias() | BIAS < -5 | BIAS > 5 |
| MACD | calc_macd() | 金叉 | 死叉/背离 |

### 3.4 仓位控制

| 市场 | 仓位 |
|------|------|
| 牛市 (MA12>MA60) | 80% |
| 熊市 (MA12<MA60) | 20% |
| 上涨趋势 | 最高80% |
| 下跌趋势 | 最高30% |

### 3.5 止损止盈

| 类型 | 幅度 |
|------|------|
| 止损 | -5% |
| 止盈 | +15% |

---

## 四、买卖点体系

### 4.1 买点优先级

| 优先级 | 买点 | 确认条件 | 仓位 |
|--------|------|----------|------|
| ⭐⭐⭐⭐⭐ | **双重背离** | 笔背驰+MACD背离 | 80% |
| ⭐⭐⭐⭐ | **二买** | 回调不破前低 | 50% |
| ⭐⭐⭐⭐ | **三买** | 突破中枢回调不破 | 60% |
| ⭐⭐⭐ | **MACD金叉** | 水上金叉 | 40% |
| ⭐⭐⭐ | **KDJ金叉** | K>D且J>50 | 40% |
| ⭐⭐ | **BOLL下轨** | 位置<0.2 | 50% |
| ⭐⭐ | **底分型** | 底分型确认 | 30% |

### 4.2 卖点优先级

| 优先级 | 卖点 | 确认条件 |
|--------|------|----------|
| ⭐⭐⭐⭐⭐ | **双重背离** | 笔背驰+MACD顶背离 |
| ⭐⭐⭐⭐ | **顶分型** | 顶分型确认 |
| ⭐⭐⭐ | **MACD顶背离** | DIF未创新高 |
| ⭐⭐⭐ | **RSI超买** | RSI>70 |
| ⭐⭐⭐ | **KDJ死叉** | K<D |
| ⭐⭐ | **BOLL上轨** | 位置>0.8 |

---

## 五、测试结果

### 5.1 模拟测试通过率

| 测试 | 场景数 | 通过数 | 通过率 |
|------|--------|--------|--------|
| 综合策略测试 | 9 | 8 | 89% |
| 多指标测试 | 5 | 5 | 100% |

### 5.2 场景覆盖

✅ 上涨趋势 → buy  
✅ 下跌趋势 → sell  
✅ 震荡市场 → hold  
✅ 顶背离 → sell  
✅ 底背离 → buy  
✅ 突破上涨 → buy  
✅ 超买区域 → sell  
✅ 超卖区域 → buy  

---

## 六、Git提交记录

| 提交 | 描述 |
|------|------|
| be4f45c | 添加缠论多级别联立分析策略文档 |
| dcd3ce1 | 添加缠论多级别联立分析策略 |
| 12d3b52 | 添加李晓军多级别联立实盘策略 |
| 9c4c0b5 | 补充完整版策略-月线牛熊判断/仓位控制/精确买卖点 |
| a5a4bb5 | 添加30分钟短线波段策略 |
| bad561a | 添加缠论与MACD背离结合策略 |
| 2a9f86a | 添加缠论综合交易策略-统一买入卖出信号 |
| 377e5c7 | 优化综合策略信号逻辑并更新测试 |
| 00df2c7 | 优化策略-上涨趋势买入信号+仓位控制 |
| 1375e09 | 扩展模拟测试验证-通过率89% |
| 8b6de63 | 多指标策略-RSI/KDJ/BOLL/CCI/WR/BIAS + 缠论 |

---

## 七、使用说明

### 7.1 快速开始

```python
from chan_multilevel_strategy import ChanMultiLevelStrategy
from multi_indicator_strategy import MultiIndicatorStrategy

# 创建策略
strategy = MultiIndicatorStrategy()

# 分析信号
signal = strategy.analyze(bars)

# 执行交易
result = strategy.execute(signal, current_price)
```

### 7.2 数据格式

```python
bars = pd.DataFrame({
    'open': [100, 101, ...],
    'high': [102, 103, ...],
    'low': [99, 100, ...],
    'close': [101, 102, ...],
    'volume': [1000000, ...]
})
```

---

## 八、后续计划

1. [ ] 实盘对接 - 连接券商API
2. [ ] 回测系统 - 历史数据回测
3. [ ] 实时数据 - 对接实时行情
4. [ ] 策略优化 - 机器学习辅助

---

## 九、参考资源

- [czsc](https://github.com/waditu/czsc) - 缠论Python库
- [李晓军缠论](http://blog.sina.com.cn/chzhshch) - 缠中说禅博客

---

> 更新时间: 2026-03-28
> 仓库: github.com/beyondjjw/QUANTAXIS/chan_multilevel/