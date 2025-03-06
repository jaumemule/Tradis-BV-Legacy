from src.application.StopLossManager import StopLossManager
from src.infra.slackClient import Slack
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.database import Database
from src.infra.ApiClient import ApiClient
from src.infra.balancesRepository import BalancesRepository
import gc
from src.infra.walletClient import Wallet
import datetime

class StopLossWorker:

    def __init__(self, method):
        self.method = method

        # retry if we could not retrieve the minutely data
        self.retryCounter = 0

        # this load will be kept in memory for the worker
        self.configurations = EnvironmentConfigurations()

        self.database = Database(self.configurations)
        self.apiClient = ApiClient(self.configurations)
        self.slack = Slack(self.configurations.slackToken, self.configurations.environmentName, self.configurations)
        self.slack.send('StopLoss started in ' + self.configurations.environmentName + ' under mode ' + self.method)
        self.balancesRepository = BalancesRepository(self.configurations, self.database)
        self.wallet = Wallet(self.configurations)
        self.configurations.currentlyRunningMethodology = 'simulation'

        # configure this if necessary
        self.balancesRepository.staticStartTime = datetime.datetime(2018, 9, 1, 0, 0, 0)

    def work(self):
        # this could be picked up by a queue system
        strategies = self.apiClient.strategies()

        for strategy in strategies:
            if strategy['active'] == True:
                self.fire(strategy)

    def fire(self, strategy):

        print('to adapt accounts, aborting')

        return

        # TODO add accounts instead of strategies
        process: StopLossManager = StopLossManager(
            self.configurations,
            self.balancesRepository,
            self.apiClient,
            self.wallet,
            self.database,
            strategy
        )


        # TODO add accounts instead of strategies
        self.database.connectToAppropiateCollection(
            strategy
        )

        process.runStopLoss(self.method, self.balancesRepository.staticStartTime)

        del process  # remove the instance to clear memory dedicated
        gc.collect()  # tell the garbage collector to empty memory, not sure if brings value

worker = StopLossWorker('simulation')
worker.work()
