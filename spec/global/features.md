# QUANTAXIS 已有功能清单

![功能模块概览](./images/05-feature-modules.png)

## QAData — 数据模块

- **QADateTR:** 日期时间处理与转换
- **QADatastructure:** DataFrame/Series 数据结构
- **QAData_Free:** 免费数据接口
- **QAData_Save:** 数据持久化存储

## QAFetch — 数据获取

- **QA fetch stock min:** 获取股票分时数据
- **QA fetch stock day:** 获取股票日线数据
- **QA fetch index:** 获取指数数据
- **QA fetch futures:** 获取期货数据
- **QA fetch option:** 获取期权数据
- **TuShare adapter:** TuShare API 集成
- **Tdx adapter:** 通达信数据接口

## QASU — 数据存储

- **QA_SU_save:** 数据存储到 MongoDB
- **QA_SU_save_tushare:** TuShare 数据存储
- **QA_SU_save_future:** 期货数据存储
- **QA_SU_update:** 增量更新

## QAStrategy — 策略模块

- **QASTRATEGY:** 策略基类
- **QA_Stock_IPV:** 股票池策略
- **QA_Stock_Rela:** 关系策略
- **Signal generation:** 交易信号生成

## QAEngine — 执行引擎

- **QA_Engine:** 异步策略执行引擎
- **Event driven:** 事件驱动架构

## QAMarket — 市场接口

- **QAMarket:** 市场接口抽象
- **Broker adapter:** 券商适配器
- **Future market:** 期货市场
- **Stock market:** 股票市场
- **Crypto market:** 数字货币市场

## QIFI — 统一账户

- **QA_Z_Account:** 账户管理
- **QA_Position:** 持仓管理
- **QA_Order:** 订单管理
- **QA_Trade:** 成交记录

## QAFactor — 因子研究

- **QAFactor:** 因子计算框架
- **Alpha factors:** Alpha 因子库
- **Factor analysis:** 因子分析工具

## QAIndicator — 技术指标

- **Indicators:** 常用技术指标
- **Bollinger Bands:** 布林带
- **MACD:** 异同移动平均线
- **KDJ:** KDJ 指标

## QAWebServer — Web 服务

- **QAServer:** Tornado Web API
- **Futures server:** 期货行情服务
- **Stock server:** 股票行情服务

## QAUtil — 工具函数

- **Date util:** 日期工具
- **File util:** 文件操作
- **Config util:** 配置管理
- **Log util:** 日志工具

## QAAnalysis — 分析模块

- **Performance analysis:** 绩效分析
- **Risk metrics:** 风险指标
- **Drawdown analysis:** 回撤分析

## czsc — 缠中说禅模块

- **CZSC:** 缠论核心算法
- **笔、线段、中枢:** 缠论基本概念
- **背驰分析:** 走势背驰判断

## qapro-rs — Rust 扩展

- **QAConnector:** 高性能连接器
- **QAParser:** 数据解析器
- **QARisk:** 风险计算
- **QAFactor-rs:** Rust 因子计算
- **QAExecution:** 高频执行

---
*最后更新: 2026-03-27 — 初始化生成*
