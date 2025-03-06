from src import stoplossProcess

def trigger(args):
    source = args[0]
    datetime = args[1]
    exchange = args[2]
    basecoin = args[3]
    exchange_rates = args[4]

    print('receiving exchange rate confirmation in ', basecoin,' from ',exchange,'...', source, ' at ', datetime)

    stoplossProcess.invokeIt(exchange, basecoin, exchange_rates)
