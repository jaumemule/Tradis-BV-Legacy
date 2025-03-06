class TrackerRepository:

    def __init__(
        self,
        environmentConfigurations,
        Database
    ):
        self.Database = Database
        self.environmentConfigurations = environmentConfigurations

    def recordBtcCoinPrices(self, results: object) -> None:
        self.Database.btcCollection.insert_one(results)

    def updateOneBtcCollection(self, results: object, key) -> None:
        key = {'date': key}
        self.Database.btcCollection.update(key,{"$set": results}, upsert = True)

    def recordUsdtCoinPrices(self, results: object) -> None:
        self.Database.usdtCollection.insert_one(results)

    def updateOrInsertBinanceUsdtCollection(self, results: object, key) -> None:
        key = {'date': key}
        self.Database.binanceUsdtCollection.update(key,{"$set": results}, upsert = True)

    def updateOrInsertCoinbaseproEurCollection(self, results: object, key) -> None:
        key = {'date': key}
        self.Database.coinbaseproEurCollection.update(key,{"$set": results}, upsert = True)
