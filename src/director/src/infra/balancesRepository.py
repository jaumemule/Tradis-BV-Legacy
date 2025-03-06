import datetime
import pymongo
from bson.objectid import ObjectId

class BalancesRepository:

    def __init__(
        self,
        environmentConfigurations,
        Database
    ):
        self.Database = Database
        self.environmentConfigurations = environmentConfigurations

        self.loadedDataPer60MinutesInMemory = False
        self.loadedDataPer20MinutesInMemory = False

        self.lastHourItLoadedAChunckOfDataForHourlyLoads = 25 # by default will never be coincident

        # only used for simulations
        self.staticStartTime = 0

    def ourCurrentBalances(self, method: str, sandboxInitialFixture, now) -> list:

        # if we are in sandbox or lazy mode
        if method != self.environmentConfigurations.runMethodologyProduction:

            # now = datetime.datetime.utcnow()   # to be used only in production
            # if self.environmentConfigurations.currentlyRunningMethodology == 'simulation' or self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox':
            #     now = self.staticStartTime

            findDate = now # start 300 hours before

            untilBackup = now + datetime.timedelta(hours=- 170)

            data_chunk = list(self.Database.sandboxTransactionsCollection.find({"date": {'$gte': untilBackup, '$lte': findDate}}))

            if len(data_chunk) == 0:
                print('initialising sandbox balance')
                last_entry = sandboxInitialFixture

            else:
                # IS THIS A BUG?
                data_chunk = data_chunk[::-1]  # revert it

                # print(len(data_chunk), data_chunk[0]['date'])
                last_entry = data_chunk[0]

            # print('previous balance', str(last_entry['date']))

            # print('....---.... balance: ',now, last_entry)

            for ignoreCoin in self.environmentConfigurations.ignoreCoinsInBalance:
                if ignoreCoin in last_entry['balances']:
                    del last_entry['balances'][ignoreCoin]

            return last_entry

        # TODO make production code here
        # ...

    def calculateAndSaveSandboxTransaction(self, last_balance, transactions: list, accountName, presetRunDateTime = False) -> None:

        date = datetime.datetime.utcnow()
        if self.environmentConfigurations.currentlyRunningMethodology == 'simulation' or self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox':
            date = self.staticStartTime

        if presetRunDateTime != False:
            date = presetRunDateTime

        new_balances = dict(zip(last_balance.index, list(last_balance["balances"])))

        if transactions:
            if 'repeated' in transactions[accountName]:
                transactions[accountName]['repeated'] = list(transactions[accountName]['repeated'])

        transactions_and_balance = {"date": date, "transactions": transactions, "balances": new_balances}

        self.Database.sandboxTransactionsCollection.insert_one(transactions_and_balance)

    def recordAccountResults(self, results: object, is_lead_account = False) -> None:

        # for easier internal exportation, use a collection apart
        if is_lead_account:
            self.Database.sandboxTradingHistory.insert_one(results)

        self.Database.tradesCollection.insert_one(results)

    def recordActions(self, results: object) -> None:
        self.Database.actions.insert(results, check_keys=False)

    def duplicateStrategyForSimulations(self, strategy: dict) -> dict:

        strategyDuplication = {
            "active": True,
            "activelyTrading": True,
            "runOnMode": "simulation",
            "baseCoin": strategy['baseCoin'],
            "agentName": strategy['agentName'],
            "trailingsPercentageConfig": strategy['trailingsPercentageConfig'],
            "modelFileName": strategy['modelFileName'],
            "lockingConfigurationInMinutes": strategy['lockingConfigurationInMinutes'],
            "agentClassName": strategy['agentClassName'],
            "exchange": strategy['exchange'],
            "currentCoins": strategy['currentCoins'],
            "runAtMinutes": strategy['runAtMinutes'],
            "exchangeAccountName": strategy['exchangeAccountName'],
            "strategyName": strategy['strategyName'] + '_simulation_' + str(datetime.datetime.utcnow()),
            "revertMarket": strategy['revertMarket'],
            "lastOrders": strategy['lastOrders'],
            "exchangeMarkets": strategy['exchangeMarkets'],
            "sandboxInitialBalances": strategy['sandboxInitialBalances'],
            "trailings": strategy['trailings'],
            "mlEnvConfigs": strategy['mlEnvConfigs'],
            "isSimulation": True,
        }

        id = self.Database.strategies.insert(strategyDuplication, check_keys=False)

        strategyDuplication['_id'] = id

        return strategyDuplication

    def deleteStrategy(self, strategyId: dict) -> None: # only for simulations
        self.Database.strategies.delete_one({'_id' : strategyId})

    def recordAIObservations(self, results: object) -> None:
        self.Database.ai_observations.insert(results, check_keys=False)

    def recordAIQvalues(self, results: object) -> None:
        self.Database.ai_qvalues.insert(results, check_keys=False)

    def saveError(self, error: object) -> None:
        self.Database.sandboxErrorLogging.insert_one(error).inserted_id

    def retrieveActions(self, fromDate, untilDate) -> list:
        return list(self.Database.actions.find({"date": {'$gt': fromDate, '$lte': untilDate}}))

    def findStrategy(self, id) -> dict:
        return self.Database.strategies.find_one({'_id': ObjectId(id)})

    def lockStrategyTemporarily(self, strategyId, untilTime):

        if not isinstance(untilTime, datetime.date):
            raise ValueError('Expecting a date object')

        self.Database.strategies.update_one({'_id': ObjectId(strategyId)}, {"$set": {'lockedUntilDate': untilTime}}, upsert=False)

    def updateCurrentCoinsPredictionInStrategy(self, strategyId, coins: list):

        self.Database.strategies.update_one({'_id': ObjectId(strategyId)}, {"$set": {'currentCoins': coins}}, upsert=False)

    def updateStrategyLastOrdersAtOpenPrice(self, strategyId, predictions: list, exchange_rates: dict):

        orders = {}
        for coin in predictions:
            orders[coin] = exchange_rates[coin]["p"]

        strategyField = {'lastOrders' : orders}
        self.Database.strategies.update_one({'_id': ObjectId(strategyId)}, {"$set": strategyField}, upsert=False)

    def retrieveCoinsPriceAtSpecificDatetime(self, datetimeToSearch, base_coin='BTC'):

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        if base_coin == 'BTC':
            if self.environmentConfigurations.currentlyRunningMethodology == 'simulation' or self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox':
                collection = self.Database.BtcBinanceAggregation
            else:
                collection = self.Database.BtcCollection

        elif base_coin in fallbackCoins:
            collection = self.Database.UsdtCollection

        else:
            raise NotImplementedError('No collection for the current base coin')

        if self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox':
            datetimeToSearch = self.staticStartTime

        findDate = datetimeToSearch
        untilBackup = datetimeToSearch + datetime.timedelta(minutes =- 5)

        # data = list(collection.find({"date": {'$gte': untilBackup, '$lt': findDate}}))

        # TODO remove this hardcoded coins and add them to the strategy
        if base_coin == 'BTC':
            data = list(collection.find({"date": {'$gte': untilBackup, '$lte': findDate}}, {'TUSD.v': 1, 'TUSD.p': 1, 'date': 1}))
        elif base_coin in fallbackCoins:
            data = list(collection.find({"date": {'$gte': untilBackup, '$lte': findDate}}, {'BTC.v': 1, 'BTC.p': 1, 'ETH.v': 1, 'ETH.p': 1, 'check.v': 1, 'check.p': 1, 'date': 1}))
        else:
            raise NotImplementedError('base coin missing in db')
        data.reverse()

        if len(data) == 0:
            raise Exception('Not enough exchange rates in storage to perform an operation at: ' + str(findDate) + ' ' + str(untilBackup) + ' in collection ' + str(collection))
        else:
            firstEntry = data[0]

        # cast to float (store floats instead?)
        for key, item in firstEntry.items():
            if (key != 'date' and key !='_id'):
                for k, i in item.items():
                    firstEntry[key][k] = float(i)

        firstEntry[base_coin] = {'p': 1}  # Add extra for reference currency

        return firstEntry

    # FOR PREDICTIONS
    def retrieve_data_by_one_indicator_and_period_of_time(self, untilBackup, findDate, coin_index, base_coin='USDT'):

        collection = self.Database.UsdtCollection

        if base_coin == 'BTC':
            collection = self.Database.BtcCollection

        if base_coin == 'BTC' and (self.environmentConfigurations.currentlyRunningMethodology == 'simulation' or self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox'):
            collection = self.Database.BtcBinanceAggregation

        data = list(collection.find({"date": {'$lte': findDate, '$gt': untilBackup}}, {coin_index: 1, 'date': 1}).sort("date", pymongo.ASCENDING) )

        return data

    def remove_data(self, untilBackup, findDate):
        # Obvious warning - watch out what you are doing
        query = {"date": {'$lte': findDate, '$gt': untilBackup}}
        collection = self.Database.UsdtCollection
        collection.remove(query)

    def dropSimulationCollections(self):
        self.Database.sandboxTradingHistory.drop()
        self.Database.sandboxTransactionsCollection.drop()
        self.Database.tradesCollection.drop()
        self.Database.sandboxTradingHistory.drop()
        self.Database.actions.drop()
