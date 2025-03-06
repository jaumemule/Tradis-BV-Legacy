from src import Director

def predict(args):
    source = args[0]
    datetime = args[1]
    exchange = args[2]
    basecoin = args[3]
    exchange_rates = args[4]

    Director.predict(exchange, basecoin, exchange_rates)

def processAccounts(args):
    source = args[0]
    at = args[1]
    strategy = args[2]
    predictions = args[3]
    exchange_rates = args[4]
    accounts = args[5]
    isStrategyLockedToTrade = args[6]

    Director.processAccounts(strategy, accounts, predictions, at, exchange_rates, source, isStrategyLockedToTrade)
