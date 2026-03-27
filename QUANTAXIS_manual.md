# QUANTAXIS 使用手册

## 目录
1. [快速开始](#1-快速开始)
2. [数据获取](#2-数据获取)
3. [策略编写](#3-策略编写)
4. [回测分析](#4-回测分析)
5. [实盘交易](#5-实盘交易)
6. [因子计算](#6-因子计算)
7. [Web服务](#7-web服务)
8. [常见问题](#8-常见问题)

---

## 1. 快速开始

### 安装
```bash
cd /vol1/1000/openclaw/ws/QUANTAXIS
pip install -r requirements.txt
```

### 快速测试
```python
import QUANTAXIS as QA

# 获取股票数据
df = QA.QA_fetch_stock_day('000001', '2024-01-01', '2024-12-31')

# 简单策略回测
from QUANTAXIS.QAStrategy import QAStockStrategy

class MyStrategy(QAStockStrategy):
    def on_bar(self, bar):
        if bar.close > bar.open:
            self.buy()
        else:
            self.sell()
```

### 命令行工具
```bash
# 数据更新
python -m QUANTAXIS save stock_day

# 启动Web服务
python -m QUANTAXIS web

# 查看帮助
python -m QUANTAXIS --help
```

---

## 2. 数据获取

### 支持的数据源

| 数据源 | 模块 | 说明 |
|-------|------|------|
| Tushare | QATushare | 需要 token |
| 通达信 | QATdx | 实时行情/本地文件 |
| 东方财富 | QABaostock | 免费数据 |
| 聚宽 | QAJQData | 需要账号 |
| 掘金 | QAGM | 量化平台 |

### 获取日线数据
```python
from QUANTAXIS.QAFetch import QAQuery

# 获取单只股票
df = QAQuery.QA_fetch_stock_day(
    code='000001',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# 获取多只股票
df = QAQuery.QA_fetch_stock_day(
    code=['000001', '000002'],
    start_date='2024-01-01'
)
```

### 获取分钟数据
```python
# 5分钟线
df = QAQuery.QA_fetch_stock_min(
    code='000001',
    start_date='2024-01-01 09:30:00',
    end_date='2024-01-01 15:00:00',
    frequency='5min'
)
```

### 获取实时行情
```python
from QUANTAXIS.QAFetch import QATdx

# 通达信实时行情
df = QATdx.QA_fetch_get_stock_realtime('000001')
```

---

## 3. 策略编写

### 基本结构
```python
from QUANTAXIS.QAStrategy import QAStockStrategy

class MyStrategy(QAStockStrategy):
    name = '我的策略'
    
    def on_init(self):
        """初始化"""
        self.params = {
            'fast': 10,
            'slow': 20,
        }
    
    def on_bar(self, bar):
        """每个Bar回调"""
        # 获取当前持仓
        position = self.positions.get('000001', 0)
        
        # 买入逻辑
        if position == 0 and self.cross_up():
            self.buy(
                code='000001',
                price=bar.close,
                volume=100
            )
        
        # 卖出逻辑
        elif position > 0 and self.cross_down():
            self.sell(
                code='000001',
                price=bar.close,
                volume=100
            )
```

### 策略参数
```python
class MyStrategy(QAStockStrategy):
    def init(self):
        # 设置参数
        self.set_params({
            'fast_ma': 10,    # 快速均线周期
            'slow_ma': 20,    # 慢速均线周期
            'volume_min': 1000000,  # 最小成交量
        })
    
    def on_bar(self, bar):
        # 使用参数
        if bar.volume > self.params['volume_min']:
            # 交易逻辑
            pass
```

### 技术指标使用
```python
from QUANTAXIS.QAIndicator import QAIndicator

class MaStrategy(QAStockStrategy):
    def on_bar(self, bar):
        # 计算均线
        ma5 = QAIndicator.MA(self.data, 5)
        ma20 = MAIndicator.MA(self.data, 20)
        
        # 金叉买入
        if ma5[-1] > ma20[-1] and ma5[-2] <= ma20[-2]:
            self.buy()
```

---

## 4. 回测分析

### 基本回测
```python
from QUANTAXIS.QAStrategy import QABacktest

# 创建策略
strategy = MyStrategy()

# 运行回测
backtest = QABacktest(
    strategy=strategy,
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_cash=1000000,
    commission=0.0003
)

result = backtest.run()

# 查看结果
print(result.analysis())
```

### 回测结果分析
```python
# 收益分析
print(result.annual_return())    # 年化收益
print(result.sharpe_ratio())       # 夏普比率
print(result.max_drawdown())      # 最大回撤
print(result.win_rate())           # 胜率

# 交易统计
print(result.total_trades())      # 总交易次数
print(result.trade_list())        # 交易明细
```

### 高级回测
```python
from QUANTAXIS.QAStrategy import QACrossValidationBacktest

# 交叉验证回测
cv_backtest = QACrossValidationBacktest(
    strategy=MaStrategy,
    start_date='2023-01-01',
    end_date='2024-12-31',
    n_splits=5  # 5折交叉验证
)

result = cv_backtest.run()
print(result.cv_scores())
```

---

## 5. 实盘交易

### 配置账户
```python
from QUANTAXIS.QAMarket import QAAccount

# 创建实盘账户
account = QAAccount(
    account_id='simnow_001',
    broker='simnow',  # 华泰/中信/simnow
    auth_code='your_auth_code',
    password='your_password'
)

account.start()
```

### 交易接口
```python
# 下单
order = account.buy(
    code='000001',
    price=10.5,
    volume=100
)

# 撤单
account.cancel_order(order.order_id)

# 查持仓
position = account.positions.get('000001')

# 查资金
cash = account.cash
```

### 交易信号
```python
class RealStrategy(QAStockStrategy):
    def on_bar(self, bar):
        # 生成交易信号
        signal = self.get_signal()
        
        if signal == 'buy':
            self.buy(code='000001', price=bar.close, volume=100)
        elif signal == 'sell':
            self.sell(code='000001', price=bar.close, volume=100)
```

---

## 6. 因子计算

### 使用内置因子
```python
from QUANTAXIS.QAFactor.factors import MACD_Factor, RSI_Factor

# MACD 因子
macd = MACD_Factor()
result = macd.calc(stock_data)

# RSI 因子
rsi = RSI_Factor(period=14)
result = rsi.calc(stock_data)
```

### 因子列表

**技术因子**:
- MACD_Factor - MACD 指标
- RSI_Factor - RSI 相对强弱
- KDJ_Factor - KDJ 随机指标
- BOLL_Factor - 布林带
- CCI_Factor - 顺势指标
- WR_Factor - 威廉指标
- BIAS_Factor - 乖离率

**财务因子**:
- ROE_Factor - 净资产收益率
- ROA_Factor - 资产收益率
- GrossMargin_Factor - 毛利率
- NetProfit_Factor - 净利率

**情绪因子**:
- MFI_Factor - 资金流量
- VR_Factor - 量比
- CMF_Factor - 资金流向

### 自定义因子
```python
from QUANTAXIS.QAFactor.factors import register_factor

@register_factor('my_factor')
class MyFactor:
    name = '我的因子'
    
    def calc(self, data):
        # 计算因子值
        result = (data['close'] - data['open']) / data['open']
        return result
```

---

## 7. Web服务

### 启动Web服务
```bash
python -m QUANTAXIS web --port 8080
```

### API 接口
```python
# 获取股票数据
GET /api/stock?code=000001&start=2024-01-01&end=2024-12-31

# 获取策略列表
GET /api/strategies

# 提交策略回测
POST /api/backtest
{
    "strategy": "MaStrategy",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}

# 获取账户状态
GET /api/account
```

### WebSocket 实时数据
```python
# 客户端连接
ws = WebSocket('ws://localhost:8080/ws')

# 订阅行情
ws.send(json.dumps({
    'action': 'subscribe',
    'codes': ['000001', '000002']
}))

# 接收数据
def on_message(ws, message):
    data = json.loads(message)
    print(data['code'], data['price'])
```

---

## 8. 常见问题

### Q: 如何安装数据源?
```bash
# Tushare
pip install tushare

# 通达信
pip install pytdx

# 东方财富 (baostock)
pip install baostock
```

### Q: 数据获取失败?
```python
# 检查网络
import requests
r = requests.get('https://api.tushare.pro')

# 使用备用数据源
from QUANTAXIS.QAFetch import QABaostock
df = QABaostock.QA_fetch_stock_day('000001')
```

### Q: 回测速度慢?
```python
# 使用向量化回测
from QUANTAXIS.QAStrategy import QAVectorBacktest

# 或使用多进程
backtest = QABacktest(strategy=MyStrategy, n_jobs=4)
```

### Q: 实盘连接失败?
```python
# 检查账户配置
from QUANTAXIS.QAMarket import QAAccount
account = QAAccount()

# 测试连接
result = account.test_connection()
print(result)
```

---

## 附录

### 命令行参数
```bash
python -m QUANTAXIS --help

Options:
  --save STOCK       保存股票数据
  --save FUTURES    保存期货数据
  --web              启动Web服务
  --version          显示版本
```

### 目录结构
```
QUANTAXIS/
├── QUANTAXIS/       核心代码
├── czsc/            缠论模块
├── czsc_web/        Web前端
└── requirements.txt
```

### 相关文档
- [czsc_architecture.md](./czsc_architecture.md) - 缠论模块架构
- [QUANTAXIS_architecture.md](./QUANTAXIS_architecture.md) - 完整架构文档

---

*手册版本: 1.0*
*更新时间: 2026-03-28*
*作者: beyondjjw*