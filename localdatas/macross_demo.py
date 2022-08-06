import datetime
import backtrader as bt
from MongoHLOC import MongoHLOC as mg


# Create a subclass of Strategy to define the indicators and logic

class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30  # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        
        sma_down_level_short = bt.ind.SMA(self.data1.close, period=self.p.pfast)  # fast moving average
        sma_down_level_long = bt.ind.SMA(self.data1.close, period=self.p.pslow)  # slow moving average
        self.down_crossover = bt.ind.CrossOver(sma_down_level_short, sma_down_level_long)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.down_crossover > 0:  # if fast crosses slow to the upside
                self.buy(size=1000)  # enter long

        if self.crossover > 0:  # if fast crosses slow to the upside
            self.buy(size=2000)  # enter long

        elif self.down_crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position


code = '000629'
start = '2022-04-01'
end = '2022-07-01'

try:
    current = mg().get_data_by_30minutes(code, start, end)
    down = mg().get_data_by_5minutes(code, start, end)
except Exception as e:
    print(str(e))
    exit()

cerebro = bt.Cerebro()  # create a "Cerebro" engine instance

cerebro.broker.setcash(50000)
cerebro.broker.setcommission(0.0005)

# Create a data feed
current_data = bt.feeds.PandasData(dataname=current,
                            name=code,
                            fromdate=datetime.datetime.strptime(start, "%Y-%m-%d"),
                            todate=datetime.datetime.strptime(end, "%Y-%m-%d"),
                            timeframe=bt.TimeFrame.Days
                            )

down_data = bt.feeds.PandasData(dataname=down,
                                  name=code,
                                  fromdate=datetime.datetime.strptime(start, "%Y-%m-%d"),
                                  todate=datetime.datetime.strptime(end, "%Y-%m-%d"),
                                  timeframe=bt.TimeFrame.Minutes
                                  )

cerebro.adddata(current_data)  # Add the data feed
cerebro.adddata(down_data)  # Add the data feed

cerebro.addstrategy(SmaCross)  # Add the trading strategy
print('Start portfolio {}'.format(cerebro.broker.getcash()))
cerebro.run()  # run it all
print('End portfolio {}'.format(cerebro.broker.getcash()))

cerebro.plot(style='candle')  # and plot it with a single command
