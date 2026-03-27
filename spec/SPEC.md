# QUANTAXIS 项目开发规范 (SDD)

## 项目信息
- **名称**: QUANTAXIS 量化金融框架
- **版本**: 2.0.0 (Fork)
- **路径**: `/ws/QUANTAXIS`
- **技术栈**: Python + Rust

## 架构概览

```
QUANTAXIS/
├── QUANTAXIS/              # 核心模块 (18个)
│   ├── QAAnalysis/        # 分析
│   ├── QACmd/             # 命令行
│   ├── QAData/            # 数据结构
│   ├── QAEngine/           # 引擎
│   ├── QAFactor/           # 因子
│   ├── QAFetch/            # 数据获取
│   ├── QAIndicator/        # 指标
│   ├── QAMarket/           # 市场
│   ├── QAPubSub/           # 消息队列
│   ├── QASU/               # 数据存储
│   ├── QAStrategy/         # 策略
│   ├── QAUtil/             # 工具
│   ├── QAWebServer/        # Web服务
│   └── QIFI/               # 账户
├── czsc/                   # 缠论模块
├── czsc_web/               # Web服务
├── qapro-rs/               # Rust量化库
└── config/                # 配置
```

## 开发规范

### 1. 代码规范
- Python: PEP 8 + pylint
- Rust: cargo fmt
- 命名: 驼峰/下划线混用 (遵守原项目风格)

### 2. 模块划分
- 每个模块独立功能
- 模块内聚，模块间低耦合
- 遵循单一职责原则

### 3. 数据流
```
数据获取 → 数据处理 → 策略计算 → 信号生成 → 交易执行
(QAFetch) (QAData) (QAEngine) (QAIndicator) (QAMarket)
```

### 4. 测试要求
- 单元测试覆盖率 > 60%
- 关键函数必须测试

### 5. Git 工作流
- Feature branch 开发
- Commit message 规范
- Code review 合并

## 当前可开发功能

| 优先级 | 功能 | 模块 | 难度 |
|--------|------|------|------|
| P0 | 数据接口统一 | QAFetch | 中 |
| P1 | 因子库扩展 | QAFactor | 中 |
| P1 | 回测加速 | QAEngine + qapro-rs | 高 |
| P2 | Web 可视化 | QAWebServer | 低 |
| P2 | 飞书通知 | QAUtil | 低 |

## 环境配置
```bash
cd /ws/QUANTAXIS
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---
创建时间: 2026-03-27
规范版本: 1.0