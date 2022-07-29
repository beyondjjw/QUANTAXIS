import QUANTAXIS as QA

# Account = QA.QA_Account()
# Broker = QA.QA_BacktestBroker()



import numpy as np
import pandas as pd

import talib

print(talib.get_functions())
print(talib.get_function_groups())

def MACD_JCSC(dataframe, SHORT=12, LONG=26, M = 9):
    """
    1. DIF 向上突破 DEA， 买入信号参考
    2. DIF 向下跌破 DEA， 卖出信号参考
    """
    CLOSE = dataframe.close
    DIFF  = QA.EMA(CLOSE, SHORT) - QA.EMA(CLOSE, LONG)
    DEA   = QA.EMA(DIFF, M)
    MACD  = 2 * (DIFF - DEA)
    
    CROSS_JC = QA.CROSS(DIFF, DEA)
    CROSS_SC = QA.CROSS(DEA, DIFF)
    
    ZERO = 0
    
    return pd.DataFrame({"DIFF": DIFF, 'DEA': DEA, 'MACD': MACD, 
                         'CROSS_JC':CROSS_JC , 'CROSS_SC': CROSS_SC, 'ZERO' : 0})
    
def MACD_MJ(dataframe, SHORT=12, LONG=26, M = 9):
    """
    DIF:EMA(CLOSE,12)-EMA(CLOSE,26);
    DEA:EMA(DIF,9);
    MACD:(DIF-DEA)*2,COLORSTICK;

    红面积:SUM(MACD,BARSLAST(MACD<0))*(MACD>0),COLOR0000FF,NODRAW;
    绿面积:SUM(MACD,BARSLAST(MACD>0))*(MACD<0),COLORFFFF00,NODRAW;
    AA:=ROUND(REF(绿面积,1)*100);
    BB:=ROUND(REF(红面积,1)*100);
    DRAWNUMBER(CROSS(0,MACD),HHV(REF(MACD,1),5)+0.03,ABS(BB)),COLORMAGENTA;
    DRAWNUMBER(CROSS(MACD,0),LLV(REF(MACD,1),5)-0.03,ABS(AA)),COLORGREEN;
    """