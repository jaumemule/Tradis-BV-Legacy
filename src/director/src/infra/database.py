import pymongo
import datetime
import src.application.strategy_collection_nomenclatures as strategy_collection_nomenclatures

class Database:

    sandboxTransactionsCollection = ''
    BtcCollection = ''
    UsdtCollection = ''
    BtcHistoricalCollection = ''
    AIresults = ''
    sandboxTradingHistory = ''
    sandboxErrorLogging = ''

    # instance attribute
    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations

        self.app_client = pymongo.MongoClient(environmentConfigurations.mongoDbUrl, connect=False)

        self.ai_environment = None
        self.raw_data_and_indicators = None

        if environmentConfigurations.ai_db_enabled == True:
            try:
                self.ai_client = pymongo.MongoClient(environmentConfigurations.mongoDbAiDatabaseConnection, connect=False)
                dbAi = self.ai_client.ai

                ## AI Database
                self.ai_environment = dbAi['ai_environment']
                self.raw_data_and_indicators = dbAi['raw_data_and_indicators']
            except Exception:
                pass

        self.dbAggregated = self.app_client.aggregated

        ## Core application
        self.BtcCollection = self.dbAggregated['BTC']
        self.UsdtCollection = self.dbAggregated['USDT']
        self.EurCoinbaseProCollection = self.dbAggregated['coinbasepro_EUR']
        self.BtcHistoricalCollection = self.dbAggregated['BTC_historical']
        self.BtcBinanceAggregation = self.dbAggregated['binance_aggregation']
        self.strategies = self.dbAggregated['strategies']

        if environmentConfigurations.currentlyRunningMethodology == 'simulation':
            self.simulations_aggregation = self.dbAggregated['simulations_aggregation'] # in use for simulations

    def connectToAppropiateCollection(self, account, btcCoinsAggregationException = False, runOn='real_money'):

        dbAggregated = self.dbAggregated

        simulation_suffix = ''

        if runOn == 'simulation':
            now = datetime.datetime.utcnow()

            simulation_id = '_simulation_' + str(now)

            simulation_suffix = '_' + str(account['accountName'] + simulation_id)
            self.sandboxTransactionsCollection = dbAggregated['trading_' + simulation_suffix]
            self.sandboxTransactionsCollection.create_index("date")

        if btcCoinsAggregationException:
            self.BtcCollection = self.dbAggregated['binance_aggregation']

        # DEPRECATED BUT OLD WAY
        # nomenclature = strategy_collection_nomenclatures.generate_from_strategy_dict(strategy)

        # new approach, all results together

        self.tradesCollectionName = 'trades' + simulation_suffix
        self.tradesCollection = dbAggregated['trades' + simulation_suffix]

        # TODO this is descending for later querying the first result faster
        # that will change in the future

        if runOn == 'simulation':
            self.tradesCollection.create_index("at")
            self.tradesCollection.create_index("_account")

        # WARNING: STILL VALID FOR PROCYON RESULTS IN PRODUCTION. FOR EASIER EXPORTS
        # WARNING: STILL VALID FOR PROCYON RESULTS IN PRODUCTION. FOR EASIER EXPORTS
        # WARNING: STILL VALID FOR PROCYON RESULTS IN PRODUCTION. FOR EASIER EXPORTS
        # assess lead account
        is_lead_account = False
        if 'is_lead' in account:
            if account['is_lead'] == True:
                is_lead_account = True

        if is_lead_account:
            self.sandboxTradingHistory = dbAggregated['transactions_' + account['accountName']]

        if is_lead_account and runOn == 'simulation':
            self.sandboxTradingHistory.create_index("at")

        self.sandboxErrorLogging = dbAggregated['error_' + account['accountName'] + simulation_suffix]

    def connectToActionsCollectionByStrategy(self, strategy, runOn='real_money'):

        simulation_id = ''

        if runOn == 'simulation':
            now = datetime.datetime.utcnow()
            simulation_id = '_simulation_' + str(now)

        dbAggregated = self.dbAggregated
        self.actions = dbAggregated['actions_' + strategy['strategyName'] + simulation_id]

        if runOn == 'simulation':
            self.actions.create_index("date")

        self.ai_observations = dbAggregated['ai_observations_' + strategy['strategyName'] + simulation_id]
        self.ai_qvalues = dbAggregated['ai_qvalues_' + strategy['strategyName'] + simulation_id]
