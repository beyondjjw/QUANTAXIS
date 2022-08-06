import backtrader as bt

BTVERSION = tuple(int(x) for x in bt.__version__.split('.'))

print(BTVERSION)