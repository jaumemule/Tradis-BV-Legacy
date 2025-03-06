import traceback

from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.database import Database
from src.infra.balancesRepository import BalancesRepository
from src.infra.aiRawDataRepository import AiRawDataRepository
from src.infra.walletClient import Wallet
from src.infra.ApiClient import ApiClient
from src.application.ProcessManager import ProcessManager
from src.infra.slackClient import Slack
import requests
import gc
from datetime import datetime
import sys
from src.application.AgentFactory import AgentFactory
from datetime import timedelta
import time

from src.infra.Queueing import Queueing

class Director:

    repository: BalancesRepository

    # specify method while instantiating. so we can run different modes.
    # this can come by an env var

    def __init__(self):

        # this load will be kept in memory for the worker
        self.agent = None
        self.agentContainer = {}
        self.configurations = EnvironmentConfigurations()
        self.database = Database(self.configurations)
        self.queueing = Queueing(self.configurations)

        self.repository = BalancesRepository(self.configurations, self.database)
        self.aiRawDataRepository = AiRawDataRepository(self.configurations, self.database)

        self.wallet = Wallet(self.configurations)
        self.apiClient = ApiClient(self.configurations)

        self.Slack = Slack(self.configurations.slackToken, self.configurations.environmentName, self.configurations)
        self.Slack.send('Director worker has been initialised')

        strategies = self.apiClient.strategies()

        global __agentContainer

        for strategy in strategies:
            if strategy['active'] == True and not strategy['agentName'] in self.agentContainer:
                self.agentContainer[strategy['agentName']] = AgentFactory(self.repository, self.aiRawDataRepository, strategy, self.Slack).load()

        sys.setrecursionlimit(1500)

    def work(self, exchange, baseCoin, exchangeRates):

        strategies = self.apiClient.strategies()
        actualMinute = datetime.now().minute
        actualHour = datetime.now().hour

        atDateTime = datetime.utcnow().replace(second=0, microsecond=0)
        atDateTime += timedelta(minutes=-1)  # we store from the previous minute

        for strategy in strategies:

            if strategy['runOnMode'] == 'simulation':
                return

            self.database.connectToActionsCollectionByStrategy(strategy, strategy['runOnMode'])

            if strategy['active'] == True and strategy['baseCoin'] == baseCoin and strategy['exchange'] == exchange:

                runAtHours = [actualHour] # run every hour if not set
                if 'runAtHours' in strategy:
                    runAtHours = strategy['runAtHours']

                if actualMinute in strategy['runAtMinutes'] and actualHour in runAtHours:

                    start_time = time.time()

                    accountsInStrategy = self.apiClient.accountsByStrategy(strategy['_id'])
                    processAccounts = []

                    if not any(accountsInStrategy):
                        self.Slack.send('No accounts in strategy ' + strategy['strategyName'])
                        continue

                    try:
                        agent = self.agentContainer[strategy['agentName']]
                        predictions = agent.predict(strategy['runOnMode'], atDateTime, True, True)
                        previous_coin_hold = agent.previous_coin_hold()
                        signal_id = agent.ML_signal()
                    except Exception as e:

                        traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)

                        error = ":bangbang: *could not predict*: " + traceback_str
                        self.Slack.send(error)
                        continue

                    isStrategyLockedToTrade = False
                    if 'lockedUntilDate' in strategy:
                        locked_until_datetime = strategy['lockedUntilDate'][:-8]
                        locked_until_datetime = datetime.strptime(locked_until_datetime, '%Y-%m-%dT%H:%M')
                        # is a date object
                        if locked_until_datetime >= atDateTime:
                            self.Slack.send(
                                ':lock: Strategy '+strategy['strategyName']+' is temporarily locked for trading until '
                                + str(strategy['lockedUntilDate'])
                                + ' AI sent signal ' + str(signal_id[0])
                                )
                            # continue
                            isStrategyLockedToTrade = True

                    accountsByBatch = []
                    for account in accountsInStrategy:

                        if account['active'] == True:
                            processAccounts.append(account)

                            if len(processAccounts) > 20: # process in batches of 20

                                accountsByBatch.append(processAccounts)
                                processAccounts = []

                    # append the last ones
                    if len(processAccounts) > 0:
                        accountsByBatch.append(processAccounts)

                    for accounts in accountsByBatch:

                        # TODO order of args is important. create a VO and an specific job or method
                        self.queueing.enqueueSimpleTask(
                            self.queueing.processAccounts,
                            'Director',
                            [
                                atDateTime,
                                strategy,
                                predictions,
                                exchangeRates,
                                accounts,
                                isStrategyLockedToTrade
                            ],
                            self.queueing.directorQueue
                        )

                    processing_time = round(time.time() - start_time, 2)

                    self.Slack.send(':chart_with_upwards_trend: *Previous investment was in ' + str(previous_coin_hold)
                       + ', now AI emitted signal '+str(signal_id[0])+' (0 -> sell, 1 -> hold, 2 -> buy) for strategy '
                       + strategy['strategyName'] + '. Total enqueuing time: ' + str(processing_time) + 's.*'
                    )

                    # make strategy unactive if is locked to trade
                    if strategy['activelyTrading'] == False:
                        self.apiClient.unactiveStrategy(strategy['strategyName'])

                # activate this only when there is too much data in production
                # if actualMinute == 59 and datetime.now().hour == 12:
                #     self.tellApiTocleanOldDataInLive()

        gc.collect()  # tell the garbage collector to empty memory, not sure if brings value
        return
    # processify creates a new process in background to avoid memory leaks
    # define methodology (see environmentConfigurations)
    def fire(self, strategy, processAccounts, predictions, atDateTime, exchangeRates, source, isStrategyLockedToTrade):

        try:
            process: ProcessManager = ProcessManager(
                self.configurations,
                self.repository,
                self.wallet,
                self.apiClient,
                self.database,
            )

            process.fire(strategy, processAccounts, predictions, atDateTime, exchangeRates, source, True, isStrategyLockedToTrade)

            del process  # remove the instance to clear memory dedicated
            gc.collect()  # tell the garbage collector to empty memory, not sure if brings value

        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)
            error = ":bangbang: Director: " + traceback_str

            try:
                self.Slack.send(error)
                self.repository.saveError({'err': traceback_str, 'date' : datetime.utcnow()})

            except Exception as e:
                self.Slack.send("Could not save logs into the db")
                self.Slack.send(error)

    def tellApiTocleanOldDataInLive(self):
        # connection to API
        # TODO move this from here!!!
        if self.configurations.environmentName == 'production':
            print("CLEANING OLD DATA FROM PRODUCTION IN LIVE COLLECTION")
            headers = {'client-secret' : 'id', 'client-id' : 'secret'}
            url_wallet = self.configurations.walletUrl + '/remove-old-live-data'
            r_wallet = requests.delete(url_wallet, headers=headers)
            print("CLEANED DATA STATUS: " + str(r_wallet))

    def processAccounts(self, strategy, accounts, predictions, atDateTime, exchangeRates, source, isStrategyLockedToTrade):

        start_time = time.time()

        if len(accounts) == 0:
            return

        print('----> processing', accounts, predictions, atDateTime, source, strategy, isStrategyLockedToTrade)

        # perhaps datetime and exchange rates should be taken per batch
        worker.fire(strategy, accounts, predictions, atDateTime, exchangeRates, source, isStrategyLockedToTrade)

        processing_time = round(time.time() - start_time, 2)

        self.Slack.send('Total processing time per batch is ' + str(processing_time))


### GLOBAL RECEIVERS FROM LISTENERS ###
worker = Director()

def predict(exchange, baseCoin, exchange_rates):

    worker.work(exchange, baseCoin, exchange_rates)

def processAccounts(strategy: dict, accounts: list, predictions: list, atDateTime: str, exchangeRates: dict, source = 'Director', isStrategyLockedToTrade = True):

    worker.processAccounts(strategy, accounts, predictions, atDateTime, exchangeRates, source, isStrategyLockedToTrade)


