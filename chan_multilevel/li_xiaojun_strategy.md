# 李晓军多级别联立实盘量化交易策略

## 一、核心理念

> **大级别定方向，小级别找精确买点**
> - 大周期决定战略（做多/做空/观望）
> - 小周期决定战术（何时买、何时卖）

---

## 二、级别体系

### 2.1 五级联立体系

| 级别 | 周期 | 职责 | 关键指标 |
|------|------|------|----------|
| 月线 | 1mon | **牛熊判断** | MA12 > MA60 = 牛市 |
| 周线 | 1week | **波段方向** | 笔方向 |
| 日线 | **D** | **主操作周期** | 笔/中枢/背驰 |
| 30分钟 | 30min | **精确买卖点** | 笔/段结构 |
| 5分钟 | 5min | **仓位微调** | 1分钟笔 |

### 2.2 级别协作逻辑

```
月线(战略) → 周线(波段) → 日线(主战) → 30分(入场) → 5分(平仓)
    ↓           ↓          ↓          ↓           ↓
  方向        波段      仓位       时机        精细
```

---

## 三、方向判断

### 3.1 月线 - 牛熊分界

```python
def get_month_direction(price_data):
    ma12 = price_data['close'].rolling(12).mean()
    ma60 = price_data['close'].rolling(60).mean()
    
    if ma12.iloc[-1] > ma60.iloc[-1]:
        return '牛市'  # 只做多
    else:
        return '熊市'  # 只做空/观望
```

**规则**: 熊市期间不开新仓！

### 3.2 日线 - 趋势判断

```python
def get_daily_direction(bars):
    # 笔方向
    bi_list = identify_bi(bars)
    if not bi_list:
        return '构建中'
    
    last_bi = bi_list[-1]
    return '上涨' if last_bi.direction == 'up' else '下跌'
```

---

## 四、买卖点体系

### 4.1 买点优先级

| 优先级 | 买点 | 确认条件 | 仓位 | 风险 |
|--------|------|----------|------|------|
| ⭐⭐⭐ | **一买** | 日线下跌背驰 + 30分底分型 | 30% | 高 |
| ⭐⭐⭐⭐ | **二买** | 日线上涨中 + 30分回调不破前低 | 50% | 中 |
| ⭐⭐ | **三买** | 日线突破中枢 + 30分回调不破ZG | 20% | 低 |

### 4.2 卖点优先级

| 优先级 | 卖点 | 确认条件 |
|--------|------|----------|
| ⭐⭐⭐ | **一卖** | 日线上涨背驰 |
| ⭐⭐⭐⭐ | **二卖** | 日线下跌中 + 30分反弹不过前高 |
| ⭐⭐ | **三卖** | 跌破中枢后反弹不过ZD |

### 4.3 买卖点代码实现

```python
class BuySellPoints:
    """买卖点判断"""
    
    @staticmethod
    def first_buy(daily_beichi: bool, min30_bottom: bool) -> bool:
        """
        一买: 日线下跌背驰 + 30分底分型
        """
        return daily_beichi and min30_bottom
    
    @staticmethod
    def second_buy(daily_direction: str, min30回调不破前低: bool) -> bool:
        """
        二买: 日线上涨中 + 30分回调不破前低
        """
        return daily_direction == '上涨' and min30回调不破前低
    
    @staticmethod
    def third_buy(突破中枢: bool, 回调不破ZG: bool) -> bool:
        """
        三买: 突破中枢后回调不破ZG
        """
        return 突破中枢 and 回调不破ZG
    
    @staticmethod
    def first_sell(daily_beichi: bool) -> bool:
        """一卖: 日线上涨背驰"""
        return daily_beichi
    
    @staticmethod
    def second_sell(daily_direction: str, min30反弹高点: bool) -> bool:
        """二卖: 日线下跌 + 30分反弹不过前高"""
        return daily_direction == '下跌' and min30反弹高点
```

---

## 五、背驰检测

### 5.1 笔背驰

```python
def check_bi_beichi(bi_list: List[Bi]) -> Optional[Dict]:
    """笔背驰: 力度对比"""
    if len(bi_list) < 2:
        return None
    
    current = bi_list[-1]
    previous = bi_list[-2]
    
    # 力度 = 幅度 * 成交量
    current_force = current.force
    previous_force = previous.force
    
    # 背驰条件: 创新高/新低但力度减弱
    if current.direction == previous.direction:
        if current_force < previous_force * 0.8:
            return {
                'type': f'{current.direction}背驰',
                '减弱幅度': (previous_force - current_force) / previous_force
            }
    return None
```

### 5.2 中枢背驰

```python
def check_zhongshu_beichi(entry_change: float, exit_change: float) -> bool:
    """
    中枢背驰: 进入段力度 > 离开段力度
    """
    if entry_change > 0:  # 上涨中枢
        return exit_change > 0 and exit_change < entry_change * 0.8
    else:  # 下跌中枢
        return exit_change < 0 and abs(exit_change) < abs(entry_change) * 0.8
```

---

## 六、风控体系

### 6.1 仓位管理

| 行情 | 仓位上限 | 说明 |
|------|----------|------|
| 牛市确认 | 80% | 月线MA12>MA60 |
| 震荡市 | 50% | 无明显趋势 |
| 熊市 | 0% | 月线MA12<MA60 |

### 6.2 止损规则

| 止损类型 | 条件 | 幅度 |
|----------|------|------|
| 买入后止损 | 买入后下跌 | -5% |
| 盘整止损 | 日线笔破坏 | -3% |
| 背驰止损 | 背驰后未涨 | -8% |

### 6.3 止盈规则

| 止盈条件 | 卖出比例 |
|----------|----------|
| 日线背驰 | 50% |
| 涨幅>30% | 30% |
| 跌破MA20 | 20% |

---

## 七、实战流程

### 7.1 日线级别操作流程

```
1. 月线方向判断
   └─ 牛市? → 继续; 熊市 → 停止

2. 日线趋势判断
   └─ 上涨/下跌/盘整

3. 背驰检测
   └─ 有背驰? → 准备买卖

4. 30分钟买卖点确认
   └─ 二买/三买? → 买入

5. 5分钟精确入场
   └─ 1分钟回调结束 → 买入
```

### 7.2 示例

```python
def run_strategy(month_data, daily_data, min30_data):
    # 1. 月线方向
    month_dir = get_month_direction(month_data)
    if month_dir == '熊市':
        return {'action': 'watch', 'reason': '月线熊市'}
    
    # 2. 日线分析
    daily_analysis = analyze_daily(daily_data)
    
    # 3. 30分钟买卖点
    min30_signal = analyze_min30(min30_data)
    
    # 4. 综合信号
    if daily_analysis['direction'] == '上涨':
        if min30_signal['buy_point'] == '二买':
            return {'action': 'buy', 'position': 50%, 'reason': '日线上涨+30分二买'}
    elif daily_analysis['beichi']:
        return {'action': 'sell', 'reason': '日线背驰'}
    
    return {'action': 'watch'}
```

---

## 八、策略检查清单

- [ ] 月线方向是否为牛市？
- [ ] 日线是否有明显趋势？
- [ ] 是否出现背驰信号？
- [ ] 30分钟是否有二买/三买信号？
- [ ] 仓位是否超限？
- [ ] 止损条件是否触发？

---

## 九、注意事项

1. **只做多**: A股只能做多，忽略做空信号
2. **不追高**: 30分回调结束才能买
3. **不抄底**: 只做二买/三买，不做一买（风险高）
4. **耐心**: 日线笔需要时间等待
5. **纪律**: 止损必须执行

---

> 更新时间: 2026-03-28
> 作者: beyondjjw
> 版本: 1.0