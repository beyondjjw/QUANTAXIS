# QUANTAXIS 架构全景

![系统架构](./images/03-system-architecture.png)

## 系统组件

```
┌─────────────────────────────────────────────────────────────┐
│                      QUANTAXIS 量化框架                      │
├─────────────────────────────────────────────────────────────┤
│  Web 层 (QAWebServer)                                       │
│  - Tornado Web API                                          │
│  - Flask Admin Dashboard                                    │
│  - Jupyter Notebook                                         │
├─────────────────────────────────────────────────────────────┤
│  策略层 (QAStrategy)                                         │
│  - Strategy Base Class                                      │
│  - Backtest Engine                                          │
│  - Factor Engine (QAFactor)                                 │
├─────────────────────────────────────────────────────────────┤
│  执行层 (QAMarket / QIFI)                                    │
│  - 统一账户体系                                              │
│  - 交易执行                                                  │
│  - 风控管理                                                  │
├─────────────────────────────────────────────────────────────┤
│  数据层 (QAData)                                             │
│  - DataFrame/Series 结构                                     │
│  - 数据清洗与转换                                            │
│  - MongoDB / ClickHouse 适配器                               │
├─────────────────────────────────────────────────────────────┤
│  获取层 (QAFetch / QASU)                                     │
│  - TuShare 数据源                                           │
│  - Tdx (通达信) 接口                                         │
│  - 交易所直连                                                │
├─────────────────────────────────────────────────────────────┤
│  核心层 (QAUtil / QAEngine)                                  │
│  - 工具函数库                                                │
│  - 异步引擎                                                  │
│  - 消息总线 (QAPubSub)                                       │
├─────────────────────────────────────────────────────────────┤
│  Rust 扩展 (qapro-rs)                                        │
│  - 高性能数据解析                                            │
│  - 因子计算                                                  │
│  - 协议处理                                                  │
└─────────────────────────────────────────────────────────────┘
```

## 模块划分

| 模块 | 路径 | 职责 |
|------|------|------|
| QAData | QUANTAXIS/QAData/ | 数据结构定义、K线、股票池、组合 |
| QAFetch | QUANTAXIS/QAFetch/ | 多数据源获取（TuShare、Tdx等） |
| QASU | QUANTAXIS/QASU/ | 数据存储与更新 |
| QAStrategy | QUANTAXIS/QAStrategy/ | 策略基类、信号生成 |
| QAEngine | QUANTAXIS/QAEngine/ | 异步执行引擎 |
| QAMarket | QUANTAXIS/QAMarket/ | 市场接口、交易执行 |
| QIFI | QUANTAXIS/QIFI/ | 统一账户/资金/持仓管理 |
| QAFactor | QUANTAXIS/QAFactor/ | 因子研究框架 |
| QAIndicator | QUANTAXIS/QAIndicator/ | 技术指标计算 |
| QAWebServer | QUANTAXIS/QAWebServer/ | Web API 服务 |
| QAUtil | QUANTAXIS/QAUtil/ | 工具函数库 |
| QAPubSub | QUANTAXIS/QAPubSub/ | 消息订阅发布 |

## 数据流

![数据流](./images/04-data-flow.png)

```
数据源 → QAFetch → QAData → QAStrategy/QAEngine
                              ↓
                         绩效分析 (QAAnalysis)
                              ↓
                         QIFI账户 ←→ QAMarket → 交易所
```

## 外部集成

| 服务 | 技术细节 |
|------|---------|
| MongoDB | pymongo/motor 异步驱动，默认端口 27017 |
| ClickHouse | clickhouse-driver，OLAP 分析 |
| RabbitMQ | pika库，消息队列 |
| Tushare | REST API，需要 Token 认证 |
| pytdx | Tdx 行情接口 |

## 部署拓扑

- **开发环境:** 本地 Python venv + MongoDB
- **生产环境:** Docker Compose 或 Kubernetes
- **典型服务:** 
  - QA Web Service (Tornado)
  - MongoDB Cluster
  - ClickHouse Server
  - RabbitMQ Broker

---
*最后更新: 2026-03-27 — 初始化生成*
