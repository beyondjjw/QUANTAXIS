# QUANTAXIS 项目详细分析报告

## 1. 项目概述

### 基本信息
- **项目名称**: QUANTAXIS 2.0.0 (Fork from beyondjjw/QUANTAXIS)
- **版本**: 2.0.0.dev33
- **Python 文件数**: 261 个
- **新增模块**: czsc (缠论), qapro-rs (Rust), czsc_web 等

### 技术栈
| 组件 | 技术 |
|------|------|
| **核心语言** | Python 3.11+ / Rust |
| **数据存储** | MongoDB, ClickHouse |
| **消息队列** | RabbitMQ (eventmq) |
| **Web框架** | Tornado, Flask |
| **数据处理** | Pandas, NumPy, Numba |
| **分析工具** | TA-Lib, SciPy, StatsModels |

## 2. 项目结构

```
/ws/QUANTAXIS/
├── QUANTAXIS/              # 核心 Python 包
│   ├── QAAnalysis/         # 量化分析模块
│   ├── QACmd/              # 命令行工具
│   ├── QAData/             # 数据结构定义
│   ├── QAEngine/           # 异步任务引擎 ⚠️ Python 3.11 兼容性修复
│   ├── QAFactor/           # 因子研究
│   ├── QAFetch/            # 数据获取 (Tushare, TDX, 交易所...)
│   ├── QAIndicator/        # 技术指标
│   ├── QAMarket/           # 市场接口
│   ├── QAPubSub/           # 消息订阅发布
│   ├── QASU/               # 数据存储工具
│   ├── QASchedule/         # 任务调度
│   ├── QASetting/          # 配置管理
│   ├── QAStrategy/         # 策略回测
│   ├── QAUtil/             # 工具函数
│   ├── QAWebServer/        # Web 服务
│   └── QIFI/               # 统一账户接口
├── czsc/                   # 缠中说禅模块 (Chanlun)
│   ├── analyze.py          # 缠论分析
│   ├── objects.py          # 缠论对象定义
│   ├── gm_utils.py         # 掘金量化工具
│   └── strategies.py      # 缠论策略
├── czsc_web/               # 缠论 Web 可视化
│   ├── run_gm_web.py       # 掘金 Web
│   ├── run_jq_web.py       # 聚宽 Web
│   └── web/                # 前端资源
├── qapro-rs/               # Rust 量化分析库 ⚡高性能
│   ├── Cargo.toml          # Rust 依赖配置
│   └── src/                # Rust 源码
├── chanlun-pro/            # 缠论专业版 (空目录)
├── examples/               # 示例代码
├── config/                 # 配置文件
└── docker/                 # Docker 配置
```

## 3. 核心模块详解

### 3.1 QAFetch (数据获取)
| 模块 | 功能 |
|------|------|
| QATdx.py | 通达信数据接口 (股票/期货/期权) |
| QATushare.py | Tushare Pro 数据接口 |
| QAhuobi.py | 火币交易所接口 |
| QAbinance.py | 币安交易所接口 |
| QAEastMoney.py | 东方财富数据 |
| QAClickhouse.py | ClickHouse 查询 |
| QAfinancial.py | 财务报表数据 |

### 3.2 QAData (数据结构)
- `QADataStruct.py` - K线数据结构
- `QABlockStruct.py` - 板块结构
- `QAFinancialStruct.py` - 财务数据结构
- `paneldatastruct.py` - 面板数据结构

### 3.3 QAStrategy (策略系统)
- `qactabase.py` - CTA 策略基类
- `qamultibase.py` - 多策略组合

### 3.4 qapro-rs (Rust 高性能库)
支持高性能计算模块化设计

## 4. 已安装的依赖

### 核心依赖 ✅
```
pandas<3.0           # 数据处理
numpy                # 数值计算
pymongo==4.16.0      # MongoDB
motor==3.7.1         # 异步 MongoDB
tornado==6.5.5       # Web 框架
scipy                # 科学计算
numba                # JIT 编译加速
pyecharts==2.1.0     # 可视化图表
seaborn              # 统计绘图
```

### 数据源依赖 ✅
```
tushare              # A股数据
pytdx                # 通达信行情
clickhouse-driver    # ClickHouse
```

### 策略/分析依赖 ✅
```
backtrader           # 回测框架
empyrical            # 风险指标
pyfolio              # 业绩归因
statsmodels          # 统计模型
```

## 5. Python 3.11 兼容性问题

### 已修复的问题

1. **janus 库兼容性** ✅
   - 问题: Python 3.10+ 移除了 asyncio.loop 参数
   - 修复: 修改 `QAAsyncThread.py` 使用 `asyncio.Queue` 替代

2. **pandas 季度频率** ⚠️
   - 警告: `Q-MAR` 已弃用
   - 影响: 不影响功能，仅警告

### 待修复/注意事项

- MongoDB 必须运行才能完整导入
- janus==0.4.0 与 Python 3.11 不兼容（已用替代方案）
- 部分旧依赖可能需要降级

## 6. 可开发功能点

### 6.1 高优先级
1. **完善 chanlun-pro 模块** - 当前为空目录
2. **czsc 与 QUANTAXIS 集成** - 缠论信号接入回测系统
3. **qapro-rs Rust 模块完善** - 高性能因子计算

### 6.2 中优先级
1. **实时行情 WebSocket** - 扩展现有实时功能
2. **机器学习因子挖掘** - 结合 sklearn/tensorflow
3. **云原生部署** - Kubernetes 配置优化

### 6.3 功能增强
1. **多数据源统一接口** - 标准化不同数据源
2. **缠论自动绘图** - 基于 pyecharts
3. **绩效归因分析** - 扩展 pyfolio 功能

## 7. 开发建议

### 环境设置
```bash
# 推荐的 Python 版本
python 3.9 或 3.10  # 兼容性最佳

# 或者使用虚拟环境
python3 -m venv qa_env
source qa_env/bin/activate
pip install -r requirements.txt
```

### 开发路线图
```
Phase 1: 基础修复 (1-2周)
├── 修复 Python 3.11 兼容性问题
├── 完善 chanlun-pro 空目录
└── 建立开发测试环境

Phase 2: 功能增强 (1个月)
├── czsc 缠论模块完善
├── 回测系统优化
└── Web 可视化改进

Phase 3: 性能优化 (持续)
├── Rust 模块扩展
├── Numba JIT 加速
└── 并行计算优化
```

### 关键文件索引
| 功能 | 文件位置 |
|------|----------|
| 新增功能入口 | `QUANTAXIS/__init__.py` |
| 数据结构定义 | `QUANTAXIS/QAData/QADataStruct.py` |
| 缠论核心 | `czsc/czsc/analyze.py` |
| Rust 模块 | `qapro-rs/src/main.rs` |
| Web 服务 | `czsc_web/mongo_web.py` |

## 8. 快速开始

```python
# 1. 导入核心模块 (无需 MongoDB)
from QUANTAXIS.QAUtil.QADate import QA_util_to_datetime
from QUANTAXIS.QAData import QADataStruct

# 2. 缠论分析
from czsc.analyze import CZSC

# 3. 策略开发
from QUANTAXIS.QAStrategy.qactabase import QAStrategy

# 4. 回测运行
from QUANTAXIS.QAEngine import QAThreadEngine
```

---

*分析完成时间: 2024*
*项目路径: /ws/QUANTAXIS*
