from src.application.ProcessManager import ProcessManager
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.database import Database
from src.infra.balancesRepository import BalancesRepository
from src.infra.aiRawDataRepository import AiRawDataRepository
from src.infra.walletClient import Wallet
from src.infra.ApiClient import ApiClient
from src.application.AgentFactory import AgentFactory
from src.infra.slackClient import Slack
from datetime import datetime
from datetime import timedelta

runningMode = 'real_money'

class Worker:

    runningMode: str
    process: ProcessManager
    method: str

    def __init__(self, method):
        self.method = method
        self.runningMode = runningMode
        self.agentContainer = {}

        # this load will be kept in memory for the worker
        configurations = EnvironmentConfigurations()
        self.configurations = configurations
        self.database = Database(configurations)
        self.walletClient = Wallet(configurations)
        self.apiClient = ApiClient(configurations)
        self.BalancesRepository = BalancesRepository(self.configurations, self.database)
        self.aiRawDataRepository = AiRawDataRepository(self.configurations, self.database)
        self.BalancesRepository.staticStartTime = datetime.now()
        self.configurations.currentlyRunningMethodology = runningMode

        self.process: ProcessManager = ProcessManager(
            configurations,
            self.BalancesRepository,
            self.aiRawDataRepository,
            self.walletClient,
            self.apiClient,
            self.database
        )

        self.Slack = Slack(self.configurations.slackToken, self.configurations.environmentName, self.configurations)

        strategies = self.apiClient.strategies()

        for strategy in strategies:
            if strategy['active']:
                agent = AgentFactory(self.BalancesRepository, strategy, self.Slack).load()
                self.agentContainer[strategy['agentName']] = agent

    # we do not re-instantiate per iteration, just fire!
    # define methodology (see environmentConfigurations)
    def fire(self):
        strategies = self.apiClient.strategies()

        for strategy in strategies:
            if strategy['active']:

                self.database.connectToActionsCollectionByStrategy(
                    strategy,
                    runningMode
                )

                accountsInStrategy = self.apiClient.accountsByStrategy(strategy['_id'])

                atDateTime = datetime.utcnow().replace(second=0, microsecond=0)
                atDateTime += timedelta(minutes=-1)  # we might not have the last minute yet

                agent = self.agentContainer[strategy['agentName']]

                if strategy['agentClassName'] == 'DummyAgent':
                    agent = self.agentContainer[strategy['agentName']]
                    agent._debug(self.BalancesRepository.staticStartTime)

                predictions = agent.predict(strategy['runOnMode'], atDateTime)

                processAccounts = []
                for account in accountsInStrategy:

                    if account['active'] == True:

                        processAccounts.append(account)

                self.runOn(strategy, processAccounts, predictions)

    def runOn(self, strategy, processAccounts, predictions):

        self.configurations.runOnBasedCurrency = strategy['baseCoin']
        self.configurations.runOnStrategy = strategy['strategyName']

        print('starting debug, mode ' + runningMode)

        strategy['runOnMode'] = runningMode
        self.configurations.currentlyRunningMethodology = strategy['runOnMode']
        self.configurations.environmentName = 'production'

        self.process.fire(strategy, processAccounts, ['USDT'], datetime.now(), None, 'Director', True, False)

worker = Worker(runningMode)
worker.fire()
