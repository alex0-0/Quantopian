from functools import wraps
from pandas import DataFrame, Series
from pandas.stats import moments
import quantopian.optimize as opt


def series_indicator(col):
    def inner_series_indicator(f):
        @wraps(f)
        def wrapper(s, *args, **kwargs):
            if isinstance(s, DataFrame):
                s = s[col]
            return f(s, *args, **kwargs)
        return wrapper
    return inner_series_indicator


@series_indicator('high')
def hhv(s, n):
    return moments.rolling_max(s, n)


@series_indicator('low')
def llv(s, n):
    return moments.rolling_min(s, n)


@series_indicator('close')
def ema(s, n, wilder=False):
    span = n if not wilder else 2*n - 1
    return moments.ewma(s, span=span)


def ichimoku(s, n1=9, n2=26, n3=52):
    conv = (hhv(s, n1) + llv(s, n1)) / 2
    base = (hhv(s, n2) + llv(s, n2)) / 2

    spana = (conv + base) / 2
    spanb = (hhv(s, n3) + llv(s, n3)) / 2

    return DataFrame(dict(conv=conv, base=base, spana=spana.shift(n2),
                          spanb=spanb.shift(n2), lspan=s.close.shift(-n2)))


def initialize(context):
    '''
    The continuous_future function also takes other optional arguments.

    The offset argument allows you to specify whether you want to maintain a reference to the front contract or to a back contract. Setting offset=0 (default) maintains a reference to the front contract, or the contract with the next soonest delivery. Setting offset=1 creates a continuous reference to the contract with the second closest date of delivery, etc.

    The roll argument allows you to specify the method for determining when the continuous future should start pointing to the next contract. By setting roll='calendar', the continuous future will start pointing to the next contract as the 'active' one when it reaches the auto_close_date of the current contract. By setting roll='volume', the continuous future will start pointing to the next contract as the 'active' one when the volume of the next contract surpasses the volume of the current active contract, as long as it's withing 7 days of the auto_close_date of the current contract.
    '''
    # context.stock_sids = [sid(39840), sid(5061), sid(24), sid(46631), sid(351), sid(3951), sid(6984), sid(16841), sid(3766), sid(49506), sid(33831), sid(46598), sid(21448), sid(8132), sid(7671), sid(49791), sid(5692), sid(6295)]
    context.stock_sids = [sid(24)]
    schedule_function(trade,
                      date_rules.every_day(),
                      time_rules.market_open(hours=1))


def trade(context, data):
    total_stocks_trading = len(context.stock_sids)
    total_investment_percentage = 0.8
    percentage_per_stock = (total_investment_percentage/total_stocks_trading)
    for stock in context.stock_sids:
        stock_price_data = data.history(stock, ['high', 'low', 'close', 'price'], 104, "1d")
        ich = ichimoku(stock_price_data)[-1:]
        price = data.current(stock, 'close')
        # print(ich)
        # print(price)
        # print("max:%f"%ich['spana'].max())
        record(conv=ich['conv'], babse=ich['base'], spaba=ich['spana'], spanb=ich['spanb'], lspan=ich['lspan'])#, price=price)
        # record(conv=ich['conv'], babse=ich['base'], spaba=(ich['spana'].max()+ich['spana'].min())/2, spanb=ich['spanb'], lspan=ich['lspan'])

    return
    idle = not (context.currently_long or context.currently_short)

    if idle and long_position_ready(context, history, current):
        buy_long(context, data)
    elif context.currently_long and long_position_fail(context, history, current):
        sell_long(context, data)
    elif idle and short_position_ready(context, history, current):
        buy_short(context, data)
    elif context.currently_short and short_position_fail(context, history, current):
        sell_short(context, data)

    record(highest=context.highest, price=current['close'], lowest=context.lowest)




def long_position_ready(context, history, current):
    highest = history.max()['high']
    highs = history['high']
    ret = False
    price = current['close']
    pre_price = history['close'][-2]
    if highs[context.time_span] == highest:
        context.highest = highest
    if pre_price < context.highest and price > context.highest:
        ret = True
        log.info(highest)
        print(highs)
        log.info(price)
    return ret

def buy_long(context, data):
    cl = data.current(context.crude_oil, 'contract')
    # Distribute weights evenly between our contracts.
    weights = {cl:1.0}
    # Place orders for contracts according to weights.
    order_optimal_portfolio(objective=opt.TargetWeights(weights),
                           constraints=[])
    context.currentyly_long = True

def long_position_fail(context, history, current):
    ret = False
    if context.long_count > 5:
        thd = history[-context.long_count:-(context.long_count-5)].min()['low']
    else:
        thd = history[-context.long_count:].min()['low']
    if current['close'] < thd or context.long_count > 30:
        ret = True
    return ret

def sell_long(context, data):
    sell_off(context, data)
    context.currentyly_long = False
    context.long_count = 0

def short_position_ready(context, history, current):
    lowest = history.min()['low']
    lows = history['low']
    ret = False
    price = current['close']
    pre_price = history['close'][-2]
    if lows[context.time_span] == lowest:
        context.lowest = lowest
    if pre_price > context.lowest and price < context.lowest:
        ret = True
        log.info(lowest)
        print(lows)
        log.info(price)
    return ret

def buy_short(context, data):
    cl = data.current(context.crude_oil, 'contract')
    # Distribute weights evenly between our contracts.
    weights = {cl:-1.0}
    # Place orders for contracts according to weights.
    order_optimal_portfolio(objective=opt.TargetWeights(weights),
                           constraints=[])
    context.currentyly_short = True

def short_position_fail(context, history, current):
    ret = False
    if context.short_count > 5:
        thd = history[-context.short_count:-(context.short_count-5)].max()['high']
    else:
        thd = history[-context.short_count:].max()['high']
    if current['close'] > thd or context.short_count > 30:
        ret = True
    return ret

def sell_short(context, data):
    sell_off(context, data)
    context.short_count = 0
    context.currentyly_short = False

def sell_off(context, data):
    cl = data.current(context.crude_oil, 'contract')
    # Distribute weights evenly between our contracts.
    weights = {cl:0.0}
    # Place orders for contracts according to weights.
    order_optimal_portfolio(objective=opt.TargetWeights(weights),
                           constraints=[])

