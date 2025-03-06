import pymongo

class Database:

    # instance attribute
    def __init__(self, environmentConfigurations):
        self.client = pymongo.MongoClient(environmentConfigurations.mongoDbUrl)
        self.dbAggregated = self.client.aggregated

    def connectToAppropiateCollection(self, basedCoin):

        self.btcCollection = self.dbAggregated['BTC']
        self.binanceUsdtCollection = self.dbAggregated['USDT']
        self.coinbaseproEurCollection = self.dbAggregated['coinbasepro_EUR']
