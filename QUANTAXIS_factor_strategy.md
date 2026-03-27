# QUANTAXIS 因子分析、策略与实盘完整指南

## 目录
1. [因子分析系统](#1-因子分析系统)
2. [策略开发](#2-策略开发)
3. [回测优化](#3-回测优化)
4. [实盘交易](#4-实盘交易)
5. [完整示例](#5-完整示例)

---

## 1. 因子分析系统

### 1.1 因子架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      QAFactor 因子系统                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ 技术因子    │  │ 财务因子     │  │ 情绪因子    │           │
│  │ (10+ 个)    │  │ (8+ 个)      │  │ (5+ 个)     │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    因子注册表 (FACTOR_REGISTRY)           │ │
│  │  • 注册 -> 计算 -> 存储 -> 回测                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    因子计算引擎                           │ │
│  │  • 并行计算 • 缓存 • 因子合成                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 因子列表

#### 技术因子 (Technical)
| 因子名 | 类名 | 参数 | 说明 |
|-------|------|-----|------|
| MACD | MACD_Factor | fast=12, slow=26, signal=9 | 指数平滑异同移动平均线 |
| RSI | RSI_Factor | period=14 | 相对强弱指标 |
| KDJ | KDJ_Factor | n=9, m1=3, m2=3 | 随机指标 |
| BOLL | BOLL_Factor | period=20, std=2 | 布林带 |
| CCI | CCI_Factor | period=14 | 顺势指标 |
| WR | WR_Factor | period=14 | 威廉指标 |
| BIAS | BIAS_Factor | period=6 | 乖离率 |
| ATR | ATR_Factor | period=14 | 平均真实波幅 |

#### 财务因子 (Fundamental)
| 因子名 | 类名 | 说明 |
|-------|------|------|
| ROE | ROE_Factor | 净资产收益率 |
| ROA | ROA_Factor | 总资产收益率 |
| GrossMargin | GrossMargin_Factor | 毛利率 |
| NetProfitMargin | NetProfitMargin_Factor | 净利率 |
| DebtRatio | DebtRatio_Factor | 资产负债率 |
| CurrentRatio | CurrentRatio_Factor | 流动比率 |
| Turnover | Turnover_Factor | 存货周转率 |
| RevenueGrowth | RevenueGrowth_Factor | 营收增长率 |

#### 情绪因子 (Sentiment)
| 因子名 | 类名 | 说明 |
|-------|------|------|
| MFI | MFI_Factor | 资金流量指标 |
| VR | VR_Factor | 量比 |
| CMF | CMF_Factor |  Chaikin资金流 |
| OBV | OBV_Factor | 能量潮 |
| ADX | ADX_Factor | 趋势指标 |

#### 行业因子 (Industry)
| 因子名 | 类名 | 说明 |
|-------|------|------|
| IndustryMomentum | IndustryMomentum_Factor | 行业动量 |
| IndustryRelative | IndustryRelative_Factor | 行业相对强弱 |
| TurnoverRate | TurnoverRate_Factor | 换手率 |

### 1.3 因子使用

#### 基本用法
```python
import pandas as pd
from QUANTAXIS.QAFactor.factors import (
    MACD_Factor, RSI_Factor, KDJ_Factor, BOLL_Factor,
    ROE_Factor, GrossMargin_Factor, MFI_Factor
)

# 准备数据 (需要 columns: date, code, open, close, high, low, volume)
data = pd.read_csv('stock_data.csv')

# 计算单个因子
macd_factor = MACD_Factor()
result = macd_factor.calc(data)
print(result.head())

# 计算多个因子
from QUANTAXIS.QAFactor.factors import calculate_all_technical_factors

tech_factors = calculate_all_technical_factors(data)
print(tech_factors.columns)  # 查看所有因子列
```

#### 因子合成
```python
from QUANTAXIS.QAFactor.factors import CompositeFactor

# 组合多个因子
composite = CompositeFactor(
    factors=[
        MACD_Factor(),
        RSI_Factor(),
        BOLL_Factor()
    ],
    weights=[0.3, 0.3, 0.4]  # 权重
)

result = composite.calc(data)
```

#### 因子选股
```python
from QUANTAXIS.QAFactor.factors import FactorSelector

# 基于因子选股
selector = FactorSelector(
    factors=['macd', 'rsi', 'roe'],
    top_n=10,  # 选前10只
    ascending=False  # 降序排列
)

selected_stocks = selector.select(data)
print(selected_stocks)
```

### 1.4 自定义因子
```python
from QUANTAXIS.QAFactor.factors.base import register_factor, BaseFactor

@register_factor('price_momentum')
class PriceMomentumFactor(BaseFactor):
    name = '价格动量'
    description = 'N日内收益率'
    
    def calc(self, data, n=20):
        """计算N日动量"""
        return data.groupby('code').apply(
            lambda x: (x['close'].pct_change(n))
        )

# 使用自定义因子
factor = PriceMomentumFactor()
result = factor.calc(data, n=20)
```

### 1.5 因子分析
```python
from QUANTAXIS.QAFactor.analysis import FactorAnalysis

# 因子分析
analysis = FactorAnalysis(factor_data)

# 因子收益分析
ic = analysis.calc_ic()  # 信息系数
print(f'IC均值: {ic.mean():.4f}')
print(f'IC胜率: {(ic > 0).mean():.2%}')

# 因子分组回测
returns_by_group = analysis.calc_group_returns()
print(returns_by_group)

# 因子衰减分析
decay = analysis.calc_decay(n_days=20)
print(decay)
```

---

## 2. 策略开发

### 2.1 策略架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       策略系统架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    QAStockStrategy                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │ │
│  │  │ on_init()   │ │ on_bar()    │ │ on_trade()  │          │ │
│  │  │ 初始化       │ │ K线回调     │ │ 成交回调    │          │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘          │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │ │
│  │  │ on_order()  │ │ on_cancel() │ │ on_timeout()│          │ │
│  │  │ 订单回调    │ │ 撤单回调    │ │ 超时回调    │          │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    信号生成 -> 下单                        │ │
│  │  • 技术指标计算                                            │ │
│  │  • 因子选股                                                │ │
│  │  • 仓位管理                                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 策略模板

#### 基础模板
```python
from QUANTAXIS.QAStrategy import QAStockStrategy
import pandas as pd

class MyStrategy(QAStockStrategy):
    """我的策略"""
    name = 'MyStrategy'
    
    def init(self):
        """初始化 - 只执行一次"""
        # 策略参数
        self.params = {
            'fast_ma': 10,
            'slow_ma': 20,
            'volume_threshold': 1000000,
            'position_size': 0.3,  # 30% 仓位
        }
        
        # 初始化变量
        self.data_dict = {}
        
        print(f"策略初始化: {self.name}")
    
    def on_bar(self, bar):
        """
        每个K线回调
        bar: 当前的K线数据
        """
        code = bar.code
        current_price = bar.close
        
        # 获取历史数据
        hist = self.data[code]
        
        # 计算技术指标
        ma10 = hist['close'].rolling(10).mean().iloc[-1]
        ma20 = hist['close'].rolling(20).mean().iloc[-1]
        
        # 交易逻辑
        position = self.positions.get(code, 0)
        
        if position == 0:  # 无持仓
            # 金叉买入
            if ma10 > ma20 and bar.volume > self.params['volume_threshold']:
                self.buy(
                    code=code,
                    price=current_price,
                    volume=self.params['position_size']
                )
                
        else:  # 有持仓
            # 死叉卖出
            if ma10 < ma20:
                self.sell(
                    code=code,
                    price=current_price,
                    volume=position
                )
    
    def on_trade(self, trade):
        """成交回调"""
        print(f"成交: {trade.code} {trade.direction} {trade.volume}@{trade.price}")
    
    def on_order(self, order):
        """订单回调"""
        print(f"订单: {order.status} {order.order_id}")
```

#### 因子选股策略
```python
class FactorStrategy(QAStockStrategy):
    """因子选股策略"""
    
    def init(self):
        # 因子列表
        self.factors = ['macd', 'rsi', 'roe']
        self.rebalance_days = 5  # 每5天调仓
        self.days = 0
    
    def on_bar(self, bar):
        self.days += 1
        
        # 调仓日
        if self.days % self.rebalance_days == 0:
            self.rebalance()
    
    def rebalance(self):
        """调仓"""
        # 获取因子数据
        factor_data = self.get_factor_data(self.factors)
        
        # 因子选股
        top_stocks = self.factor_select(factor_data, top_n=10)
        
        # 调仓
        current = set(self.positions.keys())
        target = set(top_stocks)
        
        # 卖出不在目标列表的
        for code in current - target:
            self.sell_all(code)
        
        # 买入目标股票
        for code in target:
            self.buy(
                code=code,
                price=self.get_current_price(code),
                volume=1.0 / len(target)  # 均匀分配
            )
```

#### 网格交易策略
```python
class GridStrategy(QAStockStrategy):
    """网格交易策略"""
    
    def init(self):
        self.grid_levels = 10      # 网格层数
        self.grid_space = 0.05     # 5% 间隔
        self.base_position = 0.5  # 基础仓位
    
    def on_bar(self, bar):
        code = bar.code
        price = bar.close
        
        # 计算网格价格
        base_price = self.get_baseline(code)
        
        for i in range(self.grid_levels):
            lower = base_price * (1 - (i + 1) * self.grid_space)
            upper = base_price * (1 - i * self.grid_space)
            
            # 下跌买入
            if price <= lower and not self.has_position(code, i):
                self.buy(code, price, volume=0.1, comment=f'grid_{i}')
            
            # 上涨卖出
            elif price >= upper and self.has_position(code, i):
                self.sell(code, price, volume=0.1, comment=f'grid_{i}')
```

### 2.3 策略信号

#### 信号类型
```python
# 买入信号
self.buy(code, price, volume)  # 开多
self.buy_open(code, price, volume)  # 开多

# 卖出信号
self.sell(code, price, volume)  # 平多
self.sell_close(code, price, volume)  # 平多

# 止损
self.stop_loss(code, price)

# 止盈
self.take_profit(code, price)
```

#### 信号条件
```python
# 技术指标信号
def get_signal(self, code):
    data = self.data[code]
    
    # MACD 金叉
    macd = MACD_Factor().calc(data)
    if macd['dif'][-1] > macd['dea'][-1] and macd['dif'][-2] <= macd['dea'][-2]:
        return 'buy'
    
    # RSI 超卖
    rsi = RSI_Factor().calc(data)
    if rsi['rsi'][-1] < 30:
        return 'buy'
    
    return 'hold'
```

---

## 3. 回测优化

### 3.1 回测流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        回测流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 准备数据                                                    │
│     └── 日线/分钟线/因子数据                                     │
│           ▼                                                      │
│  2. 策略初始化                                                  │
│     └── on_init() 执行一次                                      │
│           ▼                                                      │
│  3. 遍历K线                                                      │
│     └── on_bar() 逐K线回调                                      │
│           ▼                                                      │
│  4. 信号生成                                                    │
│     └── 技术指标/因子/规则                                       │
│           ▼                                                      │
│  5. 订单执行                                                    │
│     └── 下单/成交/仓位更新                                      │
│           ▼                                                      │
│  6. 绩效计算                                                    │
│     └── 收益率/回撤/胜率                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 回测配置
```python
from QUANTAXIS.QAStrategy import QABacktest

# 回测配置
config = {
    'strategy': MyStrategy,       # 策略类
    'start_date': '2023-01-01',  # 开始日期
    'end_date': '2024-12-31',    # 结束日期
    'initial_cash': 1000000,     # 初始资金
    'commission': 0.0003,        # 手续费
    'slippage': 0.001,           # 滑点
    'margin': 1.0,              # 保证金比例 (期货)
}

# 运行回测
bt = QABacktest(**config)
result = bt.run()
```

### 3.3 绩效指标
```python
# 获取绩效指标
print(f"总收益率: {result.total_return():.2%}")
print(f"年化收益: {result.annual_return():.2%}")
print(f"夏普比率: {result.sharpe_ratio():.2f}")
print(f"最大回撤: {result.max_drawdown():.2%}")
print(f"胜率: {result.win_rate():.2%}")
print(f"盈亏比: {result.profit_loss_ratio():.2f}")

# 收益曲线
result.returns.plot()

# 回撤曲线
result.drawdown.plot()

# 持仓曲线
result.positions.plot()
```

### 3.4 参数优化
```python
from QUANTAXIS.QAStrategy import ParameterOptimizer

# 参数范围
param_grid = {
    'fast_ma': [5, 10, 15, 20],
    'slow_ma': [20, 30, 40, 50],
    'volume_threshold': [500000, 1000000, 2000000]
}

# 网格搜索
optimizer = ParameterOptimizer(
    strategy=MaStrategy,
    param_grid=param_grid,
    metric='sharpe_ratio',  # 优化目标
    n_jobs=4               # 并行数
)

best_params = optimizer.optimize()
print(f"最优参数: {best_params}")
```

### 3.5 因子+策略组合
```python
class FactorBacktest(QABacktest):
    """因子增强回测"""
    
    def on_bar(self, bar):
        # 获取因子值
        factors = self.get_factors(bar.code)
        
        # 因子加权得分
        score = (
            factors['macd'] * 0.3 +
            factors['rsi'] * 0.3 +
            factors['roe'] * 0.4
        )
        
        # 因子过滤
        if score > 0.5:
            self.buy(bar.code, bar.close, volume=0.1)
```

---

## 4. 实盘交易

### 4.1 实盘架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       实盘交易架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ 策略信号    │───▶│ 交易引擎    │───▶│ 券商API    │        │
│  │             │    │             │    │             │        │
│  │ • 因子选股  │    │ • 订单管理  │    │ • 华泰      │        │
│  │ • 技术信号  │    │ • 仓位管理  │    │ • 中信      │        │
│  │ • 风控检查  │    │ • 成交确认  │    │ • simnow   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                           │                                   │
│                           ▼                                   │
│                    ┌─────────────┐                            │
│                    │  监控系统   │                            │
│                    │             │                            │
│                    │ • 日志      │                            │
│                    │ • 告警      │                            │
│                    │ • 报表      │                            │
│                    └─────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 账户配置

#### SimNow 仿真
```python
from QUANTAXIS.QAMarket import QAAccount

# SimNow 仿真账户
account = QAAccount(
    account_id='simnow_test',
    broker='simnow',
    server='simnow-cn.ctp',
    auth_code='your_auth_code',
    password='your_password'
)

# 连接
account.connect()

# 登录
account.login()
```

#### 实盘账户
```python
# 华泰证券
account_ht = QAAccount(
    account_id='ht_001',
    broker='huatai',
    app_id='your_app_id',
    auth_code='your_auth_code'
)

# 中信证券
account_zx = QAAccount(
    account_id='zx_001',
    broker='citic',
    server='citic-cn.ctp',
    account_no='your_account',
    password='your_password'
)
```

### 4.3 实盘策略

```python
class RealStrategy(QAStockStrategy):
    """实盘策略"""
    
    def init(self):
        # 风控参数
        self.max_position = 0.8     # 最大仓位 80%
        self.max_single = 0.2      # 单只最大 20%
        self.stop_loss = 0.05       # 止损 5%
        
        # 初始化账户
        self.account = QAAccount(broker='simnow')
        self.account.connect()
        
    def on_bar(self, bar):
        # 检查信号
        signal = self.generate_signal(bar.code)
        
        if signal == 'buy':
            # 检查仓位
            if self.account.positions_value < self.params['max_position']:
                self.order(
                    code=bar.code,
                    price=bar.close,
                    volume=self.calculate_size(bar.code)
                )
                
        elif signal == 'sell':
            # 检查止损
            self.check_stop_loss(bar.code, bar.close)
    
    def check_stop_loss(self, code, price):
        """止损检查"""
        position = self.account.positions.get(code)
        if position:
            cost = position.cost
            if (price - cost) / cost < -self.params['stop_loss']:
                self.sell(code, price, volume=position.volume)
    
    def calculate_size(self, code):
        """计算仓位"""
        total_value = self.account.total_value
        max_single = total_value * self.params['max_single']
        return int(max_single / 100) * 100  # 取整百
```

### 4.4 交易接口

#### 下单
```python
# 买入
order = self.account.buy(
    code='000001',
    price=10.5,
    volume=100,
    order_type='limit'  # 限价单
)

# 市价单
order_market = self.account.buy(
    code='000001',
    volume=100,
    order_type='market'
)

# 止损单
order_stop = self.account.buy(
    code='000001',
    price=10.0,
    volume=100,
    stop_price=9.5  # 止损价
)
```

#### 撤单
```python
# 撤单
self.account.cancel_order(order_id='order_123')

# 撤全部
self.account.cancel_all()
```

#### 查持仓
```python
# 所有持仓
positions = self.account.positions
print(positions)

# 单只股票持仓
pos = self.account.positions.get('000001')
print(f"持仓: {pos.volume}, 成本: {pos.cost}")
```

### 4.5 风控模块

```python
class RiskControl:
    """风控模块"""
    
    def __init__(self):
        self.max_position = 0.8
        self.max_loss_daily = 0.03
        self.max_trades = 100
    
    def pre_order(self, order, account):
        """下单前风控"""
        # 仓位检查
        if account.positions_value / account.total_value > self.max_position:
            return False, '超过最大仓位'
        
        # 止损检查
        position = account.positions.get(order.code)
        if position:
            loss = (order.price - position.cost) / position.cost
            if loss < -self.max_loss_daily:
                return False, '超过每日最大亏损'
        
        return True, 'ok'
    
    def post_order(self, order, trade):
        """成交后风控"""
        # 更新持仓
        # 发送通知
        pass

# 使用风控
risk = RiskControl()
account.set_risk_control(risk)
```

### 4.6 监控告警

```python
class Monitor:
    """监控系统"""
    
    def __init__(self, account):
        self.account = account
        self.thresholds = {
            'max_drawdown': 0.15,    # 最大回撤 15%
            'daily_loss': 0.03,     # 日亏损 3%
            'position_ratio': 0.9,  # 仓位 90%
        }
    
    def check(self):
        """检查各项指标"""
        alerts = []
        
        # 资金检查
        if self.account.today_pnl < -self.thresholds['daily_loss']:
            alerts.append(f"日亏损超过 {self.thresholds['daily_loss']:.1%}")
        
        # 仓位检查
        position_ratio = self.account.positions_value / self.account.total_value
        if position_ratio > self.thresholds['position_ratio']:
            alerts.append(f"仓位 {position_ratio:.1%} 超过阈值")
        
        # 发送告警
        if alerts:
            self.send_alert(alerts)
    
    def send_alert(self, messages):
        """发送告警"""
        for msg in messages:
            print(f"[ALERT] {msg}")
            # 可扩展: 邮件/短信/钉钉
```

---

## 5. 完整示例

### 5.1 因子选股 + 回测 + 实盘

```python
"""
完整流程: 因子选股 -> 策略回测 -> 实盘交易
"""

# ==================== 1. 因子选股 ====================
class StockSelector:
    """因子选股器"""
    
    def __init__(self):
        self.factors = {
            'macd': MACD_Factor(),
            'rsi': RSI_Factor(),
            'roe': ROE_Factor(),
            'gross_margin': GrossMargin_Factor()
        }
        self.weights = [0.2, 0.2, 0.3, 0.3]
    
    def select(self, date, top_n=20):
        # 获取当日股票池
        stocks = self.get_stock_pool(date)
        
        # 计算因子
        scores = {}
        for code in stocks:
            data = self.get_stock_data(code, date)
            if data is None or len(data) < 60:
                continue
            
            # 计算各因子
            score = 0
            for factor, weight in zip(self.factors.values(), self.weights):
                try:
                    f_value = factor.calc(data).iloc[-1]
                    score += f_value * weight
                except:
                    pass
            
            scores[code] = score
        
        # 排序选股
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_stocks[:top_n]]


# ==================== 2. 策略编写 ====================
class FactorRotationStrategy(QAStockStrategy):
    """因子轮动策略"""
    
    def init(self):
        self.selector = StockSelector()
        self.hold_days = 5
        self.counter = 0
        self.current_stocks = []
    
    def on_bar(self, bar):
        self.counter += 1
        
        # 调仓日
        if self.counter % self.hold_days == 0:
            self.rebalance()
    
    def rebalance(self):
        # 获取因子选股
        target_stocks = self.selector.select(self.current_date, top_n=10)
        
        # 调仓
        current = set(self.current_stocks)
        target = set(target_stocks)
        
        # 卖出
        for code in current - target:
            if self.positions.get(code, 0) > 0:
                self.sell(code, self.current_price(code), volume='all')
        
        # 买入
        for code in target - current:
            if self.positions.get(code, 0) == 0:
                self.buy(
                    code,
                    self.current_price(code),
                    volume=1.0 / len(target)
                )
        
        self.current_stocks = target_stocks


# ==================== 3. 回测 ====================
def run_backtest():
    """运行回测"""
    config = {
        'strategy': FactorRotationStrategy,
        'start_date': '2023-01-01',
        'end_date': '2024-12-31',
        'initial_cash': 1000000,
        'commission': 0.0003,
    }
    
    bt = QABacktest(**config)
    result = bt.run()
    
    # 绩效
    print(f"年化收益: {result.annual_return():.2%}")
    print(f"夏普比率: {result.sharpe_ratio():.2f}")
    print(f"最大回撤: {result.max_drawdown():.2%}")
    
    return result


# ==================== 4. 实盘 ====================
def run_realtime():
    """实盘运行"""
    # 创建策略
    strategy = FactorRotationStrategy()
    
    # 创建账户
    account = QAAccount(
        account_id='实盘账户',
        broker='simnow'
    )
    account.connect()
    
    # 启动实盘
    realtime = QARealtime(
        strategy=strategy,
        account=account,
        data_source='tdx'  # 通达信实时行情
    )
    
    # 启动监控
    monitor = Monitor(account)
    
    # 运行
    realtime.run()
    
    # 监控
    while True:
        monitor.check()
        time.sleep(60)


# ==================== 主程序 ====================
if __name__ == '__main__':
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else 'backtest'
    
    if mode == 'backtest':
        run_backtest()
    elif mode == 'realtime':
        run_realtime()
    else:
        print("Usage: python main.py [backtest|realtime]")
```

### 5.2 启动命令

```bash
# 回测
python main.py backtest

# 实盘
python main.py realtime

# 参数优化
python main.py optimize

# 因子分析
python main.py factor_analysis
```

---

## 总结

```
因子分析 ──▶ 策略开发 ──▶ 回测优化 ──▶ 实盘交易
    │              │             │            │
    ▼              ▼             ▼            ▼
 QAFactor     QAStock      QABacktest    QAAccount
 (26+因子)    Strategy     (绩效分析)     (实盘接口)
                │
                ▼
           因子选股 + 技术信号 + 风控
```

---

*文档版本: 1.0*
*更新时间: 2026-03-28*