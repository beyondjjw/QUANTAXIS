import datetime
import backtrader as bt

# 可以先写一个 dual thrust 策略测试一下
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def __init__(self):
        # 将第一个data给变量dataclose, close 是Lines对象
        self.dataclose = self.datas[0].close
        # 主数据源是分钟数据， 日线数据是投射分钟线加入到cerebro, 所以日线数据再画图的时候就不显示了
        self.data1.plotinfo.plot = False
        self.order = None
        print("initialization")

    def start(self, order=None):
        print("starting strategy")

    def prenext(self):
        print("prenext strategy")

    def nextstart(self):
        print("nextstart strategy")

    def next(self):
        # print("next strategy, a new bar")  #
        self.log("Close {}".format(self.data.close[0]))

    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        # print("{} {}".format(dt.isoformat(), txt))  #

    def stop(self):
        print("stop strategy")
        print(self.params.maperiod, self.broker.getvalue())

    def notify_order(self, order):
        print("notify_order strategy")