from src.application.StopLossManager import StopLossManager
from src.infra.slackClient import Slack
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.database import Database
from src.infra.ApiClient import ApiClient
from src.infra.balancesRepository import BalancesRepository
import gc
from src.infra.walletClient import Wallet
import traceback
import datetime

class StopLossProcess:

    def __init__(self):
        # retry if we could not retrieve the minutely data
        self.retryCounter = 0

        # this load will be kept in memory for the worker
        self.configurations = EnvironmentConfigurations()
        self.database = Database(self.configurations)
        self.apiClient = ApiClient(self.configurations)
        self.slack = Slack(self.configurations.slackToken, self.configurations.environmentName, self.configurations)
        self.slack.send('StopLoss started in ' + self.configurations.environmentName)
        self.balancesRepository = BalancesRepository(self.configurations, self.database)
        self.wallet = Wallet(self.configurations)

    def work(self, exchange, baseCoin, exchangeRates):
        # this could be picked up by a queue system
        strategies = self.apiClient.strategies()

        # TODO in the future, use a separate process per strategy. for scalability
        for strategy in strategies:
            if strategy['active'] == True:

                if strategy['runOnMode'] == 'simulation':
                    return

                self.database.connectToActionsCollectionByStrategy(strategy, strategy['runOnMode'])

                if strategy['active'] == True and strategy['baseCoin'] == baseCoin and strategy['exchange'] == exchange:

                    accountsInStrategy = self.apiClient.accountsByStrategy(strategy['_id'])

                    if not any(accountsInStrategy):
                        continue

                    processAccounts = []

                    accountsByBatch = []
                    for account in accountsInStrategy:

                        if account['active'] == True:
                            processAccounts.append(account)

                            if len(processAccounts) >= 20: # process in batches of 20

                                accountsByBatch.append(processAccounts)
                                processAccounts = []

                    # append the last ones
                    if len(processAccounts) > 0:
                        accountsByBatch.append(processAccounts)

                    for accounts in accountsByBatch:
                        self.__fire(strategy, accounts, exchangeRates)

    def __fire(self, strategy, accounts, exchangeRates):

        try:
            process: StopLossManager = StopLossManager(
                self.configurations,
                self.balancesRepository,
                self.apiClient,
                self.wallet,
                self.database,
                strategy,
                accounts
            )

            self.configurations.currentlyRunningMethodology = strategy['runOnMode']

            process.runStopLoss(strategy['runOnMode'], exchangeRates)

            del process  # remove the instance to clear memory dedicated
            gc.collect()  # tell the garbage collector to empty memory, not sure if brings value
        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)
            error = ":bangbang: stoploss: " + traceback_str

            try:
                self.balancesRepository.saveError({'err': traceback_str, 'date' : datetime.datetime.utcnow()})
                self.slack.send(error)
                gc.collect()  # tell the garbage collector to empty memory, not sure if brings value

            except Exception as e:
                self.slack.send("Could not save logs into the db")
                self.slack.send(error)

worker = StopLossProcess()

def invokeIt(exchange, baseCoin, exchange_rates):

    worker.work(exchange, baseCoin, exchange_rates)

