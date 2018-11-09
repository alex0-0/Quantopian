stock_sids = [sid(39840), sid(5061), sid(24), sid(46631), sid(351), sid(3951), sid(6984), sid(16841), sid(3766), sid(49506), sid(33831), sid(46598), sid(21448), sid(8132), sid(7671), sid(49791), sid(5692), sid(6295)]

def initialize(context):
    context.aapl = stock_sids
    schedule_function(trading_parameter,
                      date_rules.every_day(), 
                      time_rules.market_open(hours=1))
    
def trading_parameter(context, data):
    total_stocks_trading = len(stock_sids)
    total_investment_percentage = 0.8
    percentage_per_stock = (total_investment_percentage/total_stocks_trading)
    for stock in stock_sids:
        stock_price_data = data.history(stock, "price", 2, "1d")
        day_one_price = stock_price_data[0]
        day_two_price = stock_price_data[1]
        #get previous stock price
        #check if it went up by 1.2% or down by .6%
        if(day_two_price <= ((day_one_price)-(0.006 * day_one_price)) ):
            #check to see if you already have maximum % of this stock in your portfolio
            amount_of_stock = context.portfolio.positions[stock].amount 
            average_stock_price = context.portfolio.positions[stock].cost_basis
            dollar_value_of_stock = average_stock_price * amount_of_stock
            #if not then buy only the remainder to make it the necessary percentage(%)
            if(dollar_value_of_stock < (percentage_per_stock * 10000000)):
                percent_holding = ((dollar_value_of_stock/10000000) * 100) / 100
                percent_to_buy = 1 - percent_holding
                order_target_percent(stock, percent_to_buy)  
        elif(day_two_price >= ((0.012 * day_one_price)+day_one_price)):
            #sell all of that stock
            order_target_percent(stock, 0)