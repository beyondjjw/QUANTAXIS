# QUANTAXIS 2.0.0

量化金融框架 (Quantitative Financial Framework)

## 功能用途

开源的量化金融框架，支持：
- 多市场数据获取与存储 (MongoDB/ClickHouse)
- 统一账户体系 (股票/期货/数字货币)
- 因子研究与回测
- 策略开发与执行
- Web 服务与任务调度

## 技术栈

- **语言**: Python / Rust
- **数据库**: MongoDB, ClickHouse
- **消息队列**: RabbitMQ
- **Web框架**: Tornado
- **核心依赖**: numpy, pandas, asyncio

## 项目结构

```
QUANTAXIS/
├── QUANTAXIS/        # 核心 Python 模块
├── qapro-rs/         # Rust 量化分析
├── chanlun-pro/      # 缠论模块
├── czsc/             # 缠中说禅
├── czsc_web/         # 缠论 Web
├── docker/           # Docker 配置
├── examples/         # 示例代码
├── qabook/           # 教程
├── config/           # 配置文件
├── datas/            # 数据目录
└── localdatas/      # 本地数据
```

## 核心模块

| 模块 | 功能 |
|------|------|
| QASU/QAFetch | 数据获取与存储 |
| QAUtil | 工具函数 |
| QIFI/QAMarket | 统一账户体系 |
| QAFactor | 因子研究 |
| QAData | 数据结构 |
| QAIndicator | 自定义指标 |
| QAEngine | 异步引擎 |
| QAStrategy | 策略回测 |
| QAWebServer | Web 服务 |

## 安装

```bash
pip install quantaxis
# 或
pip install -r requirements.txt
```

---
来源: https://github.com/beyondjjw/QUANTAXIS
克隆时间: 2026-03-27
