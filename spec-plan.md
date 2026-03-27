# QUANTAXIS 因子库扩展开发计划

## 1. 项目概述

**项目名称**: QAFactor 模块扩展
**目标**: 扩展 QAFactor 模块，新增四大类量化因子
**现有基础**: QUANTAXIS/QAFactor/ 已包含基类和简单的 MA10 因子示例

---

## 2. 现有架构分析

```
QUANTAXIS/QAFactor/
├── feature.py          # QASingleFactor_DailyBase 基类（因子计算模板，数据存储）
├── featurepool.py       # 因子池示例 (MA10)
├── featureView.py      # 因子视图（查询/管理）
├── featureAnalysis.py  # 因子分析（IC/IR计算）
└── featurebacktest.py  # 因子回测

QUANTAXIS/QAIndicator/   # 已有指标库（indicators.py, talib_indicators.py）
```

**关键发现**:
- QAIndicator 已实现 MACD/RSI/KDJ/BOLL 等技术指标
- 因子基类 `QASingleFactor_DailyBase` 规范了 `calc()` 方法和数据存储
- 需将技术指标包装为符合基类规范的因子

---

## 3. 需求规格

### 3.1 技术因子 (Technical Factors)

| 因子名称 | 计算逻辑 | 数据来源 |
|---------|---------|---------|
| MACD_DIF | EMA(close,12) - EMA(close,26) | QA_indicator_MACD |
| MACD_DEA | EMA(DIF,9) | QA_indicator_MACD |
| MACD Hist | (DIF-DEA)*2 | QA_indicator_MACD |
| RSI | 相对强弱指标 | QA_indicator_RSI |
| KDJ_K | KDJ K值 | QA_indicator_KDJ |
| KDJ_D | KDJ D值 | QA_indicator_KDJ |
| KDJ_J | KDJ J值 | QA_indicator_KDJ |
| BOLL | 布林带中轨 | QA_indicator_BOLL |
| BOLL_UB | 布林带上轨 | QA_indicator_BOLL |
| BOLL_LB | 布林带下轨 | QA_indicator_BOLL |
| CCI | 商品通道指标 | QA_indicator_CCI |
| WR | 威廉指标 | QA_indicator_WR |
| BIAS | 乖离率 | QA_indicator_BIAS |

### 3.2 情绪因子 (Sentiment Factors)

| 因子名称 | 计算逻辑 | 数据来源 |
|---------|---------|---------|
| MFI | 资金流量指标 | QA_indicator_MFI |
| VR | 成交量比率 | QA_indicator_VR |
| OBV | 能量潮 | QA_indicator_OBV |
| CMF | Chaikin资金流 | 需实现 |
| large_net_inflow | 大单净流入率 | 逐笔数据 |
| retail_sentiment | 散户情绪(持仓变化) | 股东数变化 |

### 3.3 财务因子 (Financial Factors)

| 因子名称 | 计算逻辑 | 数据来源 |
|---------|---------|---------|
| revenue_growth | 营收增长率 (YoY) | 财务数据 |
| profit_growth | 净利润增长率 (YoY) | 财务数据 |
| gross_margin | 毛利率 | 财务数据 |
| net_margin | 净利率 | 财务数据 |
| roe | 净资产收益率 | 财务数据 |
| roa | 资产收益率 | 财务数据 |
| debt_to_equity | 资产负债率 | 财务数据 |
| current_ratio | 流动比率 | 财务数据 |
| quick_ratio | 速动比率 | 财务数据 |
| inventory_turnover | 存货周转率 | 财务数据 |

### 3.4 行业因子 (Industry Factors)

| 因子名称 | 计算逻辑 | 数据来源 |
|---------|---------|---------|
| industry_relative_strength | 行业相对强弱 | 行业指数对比 |
| sector_rotation | 板块轮动因子 | 动量因子 |
| industry_momentum | 行业动量 | 行业涨跌幅 |
| stock_vs_industry | 个股相对行业强弱 | 个股/行业收益差 |

---

## 4. 开发计划

### 阶段一: 基础设施扩展 (Week 1-2)

| 步骤 | 任务 | 验收标准 |
|-----|------|---------|
| 1.1 | 创建因子模块目录结构 | `QAFactor/factors/` 下建立子模块 |
| 1.2 | 扩展基类支持多字段因子 | `feature.py` 支持返回多列因子 |
| 1.3 | 创建因子基类工厂函数 | 快速生成因子类 |
| 1.4 | 添加因子注册装饰器 | `@register_factor` 装饰器 |

**产出文件**:
- `QAFactor/factors/__init__.py`
- `QAFactor/factors/base.py` - 扩展基类

### 阶段二: 技术因子开发 (Week 2-3)

| 步骤 | 任务 | 验收标准 |
|-----|------|---------|
| 2.1 | 包装 MACD 系列因子 | DIF/DEA/MACD 三个因子可单独存储 |
| 2.2 | 包装 KDJ 系列因子 | K/D/J 三个因子 |
| 2.3 | 包装 RSI/BOLL/CCI | 常用技术因子 |
| 2.4 | 包装 WR/BIAS/ATR | 辅助技术因子 |
| 2.5 | 技术因子批量计算脚本 | 按日期批量计算 |

**产出文件**:
- `QAFactor/factors/technical.py`
- `QAFactor/scripts/calc_technical_factors.py`

### 阶段三: 情绪因子开发 (Week 3-4)

| 步骤 | 任务 | 验收标准 |
|-----|------|---------|
| 3.1 | 包装 MFI/VR 因子 | 资金类因子 |
| 3.2 | 包装 OBV/CMF 因子 | 能量潮因子 |
| 3.3 | 实现大单净流入因子 | 需使用逐笔数据 |
| 3.4 | 实现股东人数变化因子 | 散户情绪代理 |

**产出文件**:
- `QAFactor/factors/sentiment.py`

### 阶段四: 财务因子开发 (Week 4-5)

| 步骤 | 任务 | 验收标准 |
|-----|------|---------|
| 4.1 | 创建财务因子基类 | 支持季报/年报数据 |
| 4.2 | 实现成长率因子 | 营收/利润增长率 |
| 4.3 | 实现盈利能力因子 | 毛利率/净利率/ROE |
| 4.4 | 实现偿债能力因子 | 资产负债率等 |
| 4.5 | 财务因子更新调度 | 季报发布后自动更新 |

**产出文件**:
- `QAFactor/factors/fundamental.py`
- `QAFactor/factors/financial_base.py`

### 阶段五: 行业因子开发 (Week 5-6)

| 步骤 | 任务 | 验收标准 |
|-----|------|---------|
| 5.1 | 实现行业分类映射 | 同花顺行业分类 |
| 5.2 | 行业相对强弱因子 | 个股/行业对比 |
| 5.3 | 板块轮动因子 | 行业动量因子 |
| 5.4 | 概念板块因子 | 概念热度因子 |

**产出文件**:
- `QAFactor/factors/industry.py`
- `QAFactor/factors/concept.py`

### 阶段六: 测试与文档 (Week 6-7)

| 步骤 | 任务 | 验收标准 |
|-----|------|---------|
| 6.1 | 单元测试 | 每个因子类测试 |
| 6.2 | 集成测试 | 因子计算+存储+查询 |
| 6.3 | 性能优化 | 大规模计算效率 |
| 6.4 | 文档编写 | README + 示例代码 |

---

## 5. 技术约束

- **Python版本**: >= 3.8
- **依赖**: pandas, numpy, clickhouse_driver, QUANTAXIS
- **数据存储**: ClickHouse factor 库
- **计算频率**: 日频 (部分财务因子为季频)

---

## 6. 文件结构规划

```
QUANTAXIS/QAFactor/
├── __init__.py
├── feature.py              # [已有] 基类
├── featurepool.py         # [已有] 示例
├── featureView.py         # [已有] 视图
├── featureAnalysis.py     # [已有] 分析
├── featurebacktest.py     # [已有] 回测
├── factors/               # [新增] 因子模块
│   ├── __init__.py
│   ├── base.py            # 扩展基类
│   ├── factory.py         # 因子工厂
│   ├── technical.py       # 技术因子
│   ├── sentiment.py       # 情绪因子
│   ├── fundamental.py     # 财务因子
│   ├── industry.py        # 行业因子
│   └── register.py        # 注册装饰器
├── scripts/                # [新增] 脚本
│   ├── calc_technical.py
│   ├── calc_sentiment.py
│   ├── calc_fundamental.py
│   └── calc_industry.py
├── tests/                  # [新增] 测试
└── docs/                   # [新增] 文档
```

---

## 7. 实现示例

### 7.1 因子基类扩展

```python
# QAFactor/factors/base.py
from QUANTAXIS.QAFactor.feature import QASingleFactor_DailyBase

class QAMultiFactor_DailyBase(QASingleFactor_DailyBase):
    """支持多字段因子的基类"""
    
    def calc(self) -> pd.DataFrame:
        """
        返回格式: pd.DataFrame with columns ['date', 'code', 'factor', 'factor2', ...]
        """
        raise NotImplementedError
```

### 7.2 因子注册装饰器

```python
# QAFactor/factors/register.py
def register_factor(name, description=""):
    """因子注册装饰器"""
    def wrapper(cls):
        cls.factor_name = name
        cls.description = description
        return cls
    return wrapper
```

### 7.3 技术因子示例

```python
# QAFactor/factors/technical.py
from QUANTAXIS.QAFactor.factors.base import QAMultiFactor_DailyBase
from QUANTAXIS.QAIndicator.indicators import QA_indicator_MACD

@register_factor("MACD", "MACD指标因子族")
class MACD_Factor(QAMultiFactor_DailyBase):
    
    def finit(self):
        self.clientr = QACKClient(...)
        self.factor_name = 'MACD_DIF'
    
    def calc(self) -> pd.DataFrame:
        data = self.clientr.get_stock_day_qfq_adv(...)
        macd = data.add_func(QA_indicator_MACD)
        return macd.reset_index().dropna()
```

---

## 8. 风险与对策

| 风险 | 对策 |
|-----|------|
| 数据源不稳定 | 因子计算增加容错，缺失数据返回空 |
| 计算量大 | 使用向量化计算，分批处理 |
| 财务因子季报延迟 | 设置财报发布日期触发器 |
| 行业分类变更 | 定期同步行业分类数据 |

---

## 9. 优先级排序

1. **P0**: 技术因子 (MACD/RSI/KDJ/BOLL) - 用户最常用
2. **P1**: 情绪因子 (MFI/VR) - 资金流向核心指标
3. **P1**: 财务因子 (ROE/毛利率) - 基本面核心
4. **P2**: 行业因子 - 进阶需求