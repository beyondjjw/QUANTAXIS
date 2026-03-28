# 缠论与MACD背离结合判断

## 一、核心理念

> **缠论结构 + MACD背离 = 双重确认**
> - 缠论提供结构 (笔/中枢/背驰)
> - MACD提供力度验证
> - 两者结合提高准确率

---

## 二、MACD基础指标

```
DIF = EMA(close, 12) - EMA(close, 26)
DEA = EMA(DIF, 9)
MACD = (DIF - DEA) * 2
```

### 背离判断

| 类型 | 条件 |
|------|------|
| **顶背离** | 价格创新高，DIF/DEA 未创新高 |
| **底背离** | 价格创新低，DIF/DEA 未创新低 |

---

## 三、结合判断逻辑

### 3.1 笔背驰 + MACD背离

```python
def check_bi_beichi_with_macd(bars: pd.DataFrame, bi_list: List[Bi], 
                               macd: Dict) -> Optional[Dict]:
    """
    笔背驰 + MACD背离 双重确认
    """
    if len(bi_list) < 2:
        return None
    
    current_bi = bi_list[-1]
    prev_bi = bi_list[-2]
    
    # 1. 笔力度背驰
    bi_beichi = current_bi.force < prev_bi.force * 0.8
    
    # 2. MACD背离
    price_high = current_bi.high > prev_bi.high
    macd_high = macd['dif'] < prev_bi['dif']
    macd_beichi = price_high and macd_high
    
    # 3. 双重确认
    if bi_beichi and macd_beichi:
        return {
            'type': '顶背离确认',
            'bi_beichi': True,
            'macd_beichi': True,
            'confidence': 0.9
        }
    
    return None
```

### 3.2 中枢背驰 + MACD背离

```python
def check_zhongshu_beichi_with_macd(bars: pd.DataFrame, zs: ZhongShu,
                                     entry_diff: float, exit_diff: float) -> Optional[Dict]:
    """
    中枢背驰 + MACD背离
    """
    if not zs:
        return None
    
    # 中枢背驰
    entry_change = (bars['close'].iloc[-1] - entry_diff) / entry_diff
    exit_change = (bars['close'].iloc[-1] - exit_diff) / exit_diff
    
    zs_beichi = False
    if zs.type == '上涨中枢':
        zs_beichi = exit_change > 0 and exit_change < entry_change * 0.8
    else:
        zs_beichi = exit_change < 0 and abs(exit_change) < abs(entry_change) * 0.8
    
    # MACD背离
    macd_beichi = entry_diff > exit_diff
    
    if zs_beichi and macd_beichi:
        return {
            'type': '中枢背驰+MACD背离',
            'confidence': 0.95
        }
    
    return None
```

---

## 四、实战应用

### 4.1 买入信号 (底背离 + 一买)

```
条件:
1. 价格创新低 (缠论笔创新低)
2. MACD DIF/DEA 未创新低 (底背离)
3. 出现底分型

信号: 一买确认
仓位: 30%
```

### 4.2 卖出信号 (顶背离 + 一卖)

```
条件:
1. 价格创新高 (缠论笔创新高)
2. MACD DIF/DEA 未创新高 (顶背离)
3. 出现顶分型

信号: 一卖确认
仓位: 清仓
```

---

## 五、代码实现

```python
class ChanMacdStrategy:
    """缠论 + MACD 背离策略"""
    
    def calc_macd(self, bars: pd.DataFrame) -> Dict:
        """计算MACD"""
        ema12 = bars['close'].ewm(span=12).mean()
        ema26 = bars['close'].ewm(span=26).mean()
        
        dif = ema12 - ema26
        dea = dif.ewm(span=9).mean()
        macd = (dif - dea) * 2
        
        return {
            'dif': dif.iloc[-1],
            'dea': dea.iloc[-1],
            'macd': macd.iloc[-1],
            'hist': macd.iloc[-1]
        }
    
    def check_divergence(self, bars: pd.DataFrame, bi_list: List[Bi]) -> Optional[Dict]:
        """检查背离"""
        if len(bi_list) < 2:
            return None
        
        macd = self.calc_macd(bars)
        current = bi_list[-1]
        prev = bi_list[-2]
        
        # 顶背离
        if current.direction == 'up':
            price_up = current.high > prev.high
            macd_up = macd['dif'] > (prev.high - prev.low)  # 简化
            
            if price_up and not macd_up:
                return {'type': '顶背离', 'confidence': 0.8}
        
        # 底背离
        else:
            price_down = current.low < prev.low
            macd_down = macd['dif'] < (prev.high - prev.low)
            
            if price_down and not macd_down:
                return {'type': '底背离', 'confidence': 0.8}
        
        return None
```

---

## 六、信号组合表

| 缠论信号 | MACD信号 | 综合信号 | 操作 |
|----------|----------|----------|------|
| 笔创新高 | DIF未创新高 | 顶背离 | 卖出 |
| 笔创新低 | DIF未创新低 | 底背离 | 买入 |
| 笔背驰 | DIF背驰 | 双重背驰 | 强卖出 |
| 笔背驰 | DIF金叉 | 背驰失败 | 持有 |
| 中枢突破 | DIF水上 | 强势 | 买入 |
| 中枢跌破 | DIF水下 | 弱势 | 卖出 |

---

> 更新时间: 2026-03-28