# QUANTAXIS 架构约束

![技术栈概览](./images/06-tech-stack.png)

## 技术栈

- **核心语言:** Python 3.x / Rust
- **数据处理:** numpy, pandas, scipy, numba
- **数据库:** MongoDB, ClickHouse
- **消息队列:** RabbitMQ / Pika
- **Web框架:** Tornado, Flask
- **异步框架:** asyncio, gevent
- **回测框架:** pybacktest, empyrical, pyfolio, alphalens
- **可视化:** matplotlib, seaborn, pyecharts

## 架构决策

- **目录结构:** Monorepo 风格，主项目 QUANTAXIS 包含多个子模块
- **分层架构:**
  - **数据层 (QAData):** 数据结构、存储、清洗
  - **获取层 (QAFetch/QASU):** 多数据源获取
  - **策略层 (QAStrategy):** 策略基类、回测引擎
  - **市场层 (QAMarket):** 交易执行、风控
  - **账户层 (QIFI):** 统一账户体系
  - **服务层 (QAWebServer):** Web API、任务调度
- **异步架构:** 基于 asyncio 的异步事件驱动
- **Rust 集成:** qapro-rs 提供高性能数据解析和计算

## API 风格

- **风格:** RESTful API (Tornado Web)
- **认证方式:** Token / Session
- **错误处理:** 统一错误码 + 详细日志

## 编码规范

- **命名约定:** 
  - 模块: 小写字母 + 下划线 (snake_case)
  - 类: 大驼峰 (PascalCase)
  - 函数/变量: 小写字母 + 下划线 (snake_case)
- **文件组织:** 每个功能模块独立目录，包含 `__init__.py`
- **代码规范:** 遵循 PEP 8，使用 pylint yapf 检查

## 部署方式

- **环境:** Linux (推荐), macOS, Windows (WSL)
- **依赖管理:** pip, poetry, Cargo (Rust)
- **容器化:** Docker / Kubernetes
- **CI/CD:** GitHub Actions

## 安全约束

- 敏感信息（API Key、数据库密码）通过环境变量配置
- 禁止硬编码凭证
- 建议使用 Docker 隔离运行环境

---
*最后更新: 2026-03-27 — 初始化生成*
