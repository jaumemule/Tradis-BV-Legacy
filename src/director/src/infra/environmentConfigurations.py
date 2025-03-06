import os

class EnvironmentConfigurations:

    ai_db_enabled: bool
    apiClientUrl: str
    __stagingApi = "http://ns3089372.ip-178-32-220.eu:3000/api/v1"
    mongoDbUrl = ''
    environmentName = ''
    walletUrl = ''
    slackToken = ''
    currentlyRunningMethodology = 'sandbox' # default

    # TODO this is rewritted once initialising the strategy process. should be gone
    userAccountList = 'default' # default

    runMethodologySandbox = 'sandbox' # just a sandbox for the money
    runMethodologyLazySandbox = 'lazy_sandbox' # avoid running predictions for faster debugging, development mode mostly
    runMethodologyProduction = 'real_money' # be careful! we are trading here :P

    # we can parametrise this in the future by a web dashboard or env variables
    tradingQuantityOfInvestmentInPercentage = [0.4, 0.3, 0.2, 0.1, 0]
    lengthOfPredictionDataInMinutes = 180
    amountOfHoursToLoadInHourlyStrategy = 100 # DEPRECATED
    maximumCoinsToTrade = 1
    minimAmountToTradeInDollars = 10 # this is bcs the userAccountList doesn't allow less than X per transaction
    slippageSecurityMarginInPercentage = 0.2 # slippage security reasons // formula: # 1000 - (1000 * (0,1 / 100))

    ignoreCoinsInBalance = ['BNB'] # we use it for fees, not for trading

    fallbackCoins = ['USDT', 'USD', 'EUR']

    walletSecret = 'id'
    walletId = 'secret'

    runOnBasedCurrency = "BTC" # default
    runOnStrategy = "" # default
    runWithVolumes = False

    def __init__(self):

        self.ai_db_enabled = True
        environment = os.getenv('ENVIRONMENT')

        if environment == 'production' or environment == 'staging':
            self.redisConnection = os.getenv('REDIS_CONNECTION')
            self.mongoDbUrl = os.getenv('MONGO_CONNECTION')
            self.mongoDbAiDatabaseConnection = os.getenv('AI_DATABASE_MONGO_CONNECTION')
            self.environmentName = environment
        elif environment == 'dev':
            self.redisConnection = 'redis://redis:6379'
            self.mongoDbUrl = 'mongodb://mongo:27017/'
            self.mongoDbAiDatabaseConnection = 'mongodb://mongo:27017/'
            self.environmentName = environment
        else:
            self.redisConnection = 'redis://localhost:6379'
            self.mongoDbUrl = 'mongodb://localhost:27017/'
            self.mongoDbAiDatabaseConnection = 'mongodb://localhost:27017/'
            self.environmentName = "dev_no_docker"

        if environment == 'production' or environment == 'staging':
            self.walletUrl = os.getenv('WALLET_URL')
            self.internalWalletUrl = os.getenv('WALLET_URL')
            self.apiClientUrl = os.getenv('WALLET_URL')
        elif environment == 'dev':
            # testing env, only in case data missing in local (tracker should be on)
            self.walletUrl = self.__stagingApi
            self.internalWalletUrl = os.getenv('WALLET_URL')
            self.apiClientUrl = 'http://api:3000/api/v1'
        else:
            # testing env, only in case data missing in local (tracker should be on)
            self.walletUrl = self.__stagingApi
            self.internalWalletUrl = 'http://localhost:8060/api/v1'
            self.apiClientUrl = 'http://localhost:8060/api/v1'

        if os.getenv('MONGO_AI_DB_ENABLED') == 'no': # patch for simulations server
            self.ai_db_enabled = False

        self.slackToken = "xxx"
