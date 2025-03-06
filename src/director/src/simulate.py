import datetime

from src.application.ProcessManager import ProcessManager
from src.application.StopLossManager import StopLossManager
from src.infra.ApiClient import ApiClient
from src.infra.balancesRepository import BalancesRepository
from src.infra.SimulationResultsRepository import SimulationResultsRepository
from src.infra.aiRawDataRepository import AiRawDataRepository
from src.infra.database import Database
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.walletClient import Wallet
from src.application.AgentFactory import AgentFactory
from src.infra.slackClient import Slack
import traceback
from src.application.AccountsContainer import AccountsContainer
import sys
from src.domain.Simulation import Simulation

runningMode = 'simulation'

class Worker:

    process: ProcessManager
    method: str

    def __init__(self,
        method,
        startAt = None,
        untilDate = None,
        sendToSlack = None,
        lockingMinutes = None,
        stoploss = False,
        jumptomarket = False,
        whaleDownPercent = None,
        whaleUpPercent = None,
        whaleMinuteLookup = None,
        takeprofit = False,
        lockStrategyAlsoForTradingBot = False,
        tradingBotsEnabled = False,
        candleSize = None,
        strategyName = None,
        ignoreStrategyLockOnHardSignal = False,
        extendLockUntilHardPrediction = False,
     ):

        sys.setrecursionlimit(500000)
        configurations = EnvironmentConfigurations()
        self.configurations = configurations

        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #
        # # # #        # # # #        # # # #             CONFIGURATIONS           # # # #        # # # #        # # # #
        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #

        self.startingDate = startAt # always set one minute less than production
        self.endDate = untilDate

        self.tradingBotsEnabled = tradingBotsEnabled
        self.forceSendSlack = sendToSlack

        self.stoplossAt = stoploss
        self.jumpToMarketAt = jumptomarket
        self.takeProfitAt = takeprofit
        self.whaleUpPercent = whaleUpPercent
        self.whaleDownPercent = whaleDownPercent
        self.whaleMinuteLookup = whaleMinuteLookup

        self.ignoreStrategyLockOnHardSignal = ignoreStrategyLockOnHardSignal

        self.lockStrategyAfterTradingMinutes = lockingMinutes  # min / None

        self.extendLockUntilHardPrediction = extendLockUntilHardPrediction

        if extendLockUntilHardPrediction:
            # lock is extended forever until there is a new hard prediction (buy or sell but not hold)
            self.lockStrategyAfterTradingMinutes = 1000000

        self.lockStrategyAlsoForStoplossAndJumpToMarket = lockStrategyAlsoForTradingBot

        self.strategyName = strategyName
        self.predict_every_minutes = candleSize

        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #
        # # # #        # # # #        # # # #          END CONFIGURATIONS          # # # #        # # # #        # # # #
        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #        # # # #

        self.method = method
        configurations.currentlyRunningMethodology = 'simulation'

        # this load will be kept in memory for the worker
        self.database = Database(configurations)

        self.apiClient = ApiClient(configurations)
        self.agentContainer = {}

        strategy = self.apiClient.strategy(self.strategyName)
        strategy['runOnMode'] = self.method
        self.runOnBaseCoin = strategy['baseCoin']

        self.account = {
                "_id": "5e7f406b5dc079add55a047f",
                "_strategy": "5db19c8b7c213e556143575e",
                "_user": "5db19c8b7c213e556143575e", # just fake it
                "accountName": strategy['strategyName'],
                "active": True,
                "is_lead": True,
                "owner": "simulations"
        }

        self.database.connectToAppropiateCollection(self.account, False, 'simulation')
        self.database.connectToActionsCollectionByStrategy(strategy, 'simulation')

        self.walletClient = Wallet(configurations)
        self.BalancesRepository = BalancesRepository(self.configurations, self.database)
        self.aiRawDataRepository = AiRawDataRepository(self.configurations, self.database)
        self.simulationResultsRepository = SimulationResultsRepository(self.configurations, self.database)

        self.BalancesRepository.staticStartTime = self.startingDate

        strategy['lockingConfigurationInMinutes'] = self.lockStrategyAfterTradingMinutes
        strategy['trailingsPercentageConfig']["stopLoss"] = self.stoplossAt
        strategy['trailingsPercentageConfig']["jumpToMarket"] = self.jumpToMarketAt
        strategy['trailingsPercentageConfig']["takeProfit"] = self.takeProfitAt
        strategy['trailingsPercentageConfig']["whaleUpPercent"] = self.whaleUpPercent
        strategy['trailingsPercentageConfig']["whaleDownPercent"] = self.whaleDownPercent
        strategy['trailingsPercentageConfig']["whaleMinuteLookup"] = self.whaleMinuteLookup
        strategy['runOnMode'] = 'simulation'

        self.coinsThatStrategyUses = [*strategy['exchangeMarkets']]
        self.firstCoinInStrategy = [*strategy['exchangeMarkets']][0]

        self.strategy = self.BalancesRepository.duplicateStrategyForSimulations(strategy)
        self.strategyId = self.strategy['_id']

        self.strategyName = self.strategy['strategyName']

        self.process = ProcessManager(
            configurations,
            self.BalancesRepository,
            self.walletClient,
            self.apiClient,
            self.database
        )

        self.Slack = Slack(self.configurations.slackToken, self.configurations.environmentName, self.configurations)

        self.agent = AgentFactory(
            self.BalancesRepository,
            self.aiRawDataRepository,
            self.strategy,
            self.Slack
        ).load(True)

        self.firedFromStudy = False

    # we do not re-instantiate per iteration, just fire!
    # define methodology (see environmentConfigurations)
    def fire(self):

        self.preRun()
        self.runOn(self.runOnBaseCoin, self.strategyName)
        self.afterRun()

    def fireFromStudy(self,):

        self.firedFromStudy = True
        self.preRun()
        self.runOn(self.runOnBaseCoin, self.strategyName)
        return self.afterRun()

    def runOn(self, basedCoin, strategyName):
        self.configurations.runOnBasedCurrency = basedCoin
        self.configurations.runOnStrategy = strategyName
        self.strategy = self.BalancesRepository.findStrategy(self.strategyId)

        atDateTime = self.BalancesRepository.staticStartTime

        predictions = self.agent.predict(self.strategy['runOnMode'], atDateTime, True, True)

        signal_id = self.agent.ML_signal()[0]

        strategyIsLocked = 'lockedUntilDate' in self.strategy and self.strategy['lockedUntilDate'] >= atDateTime
        softLock = self.ignoreStrategyLockOnHardSignal == True and signal_id == 1

        resetLock = False
        if strategyIsLocked and self.extendLockUntilHardPrediction and signal_id != 1:
            resetLock = True
            strategyIsLocked = False

        if self.endDate <= self.BalancesRepository.staticStartTime:
            print('DONE!')
            pass
        else:
            print('not yet done!', self.BalancesRepository.staticStartTime)

            # remove strategy lock because some event happened
            if resetLock == True:
                untilTime = atDateTime + datetime.timedelta(minutes=999999999)
                self.BalancesRepository.lockStrategyTemporarily(self.strategy['_id'], untilTime)
                self.strategy = self.BalancesRepository.findStrategy(self.strategyId)

            try:
                if softLock: # if hold we ignore the lock
                    self.process.fire(self.strategy, [self.account], predictions, atDateTime, None, 'Director', True, False)
                else:
                    # is a date object
                    if strategyIsLocked:
                        print('Strategy is temporarily blocked for trading after stoploss')
                    else:
                        self.process.fire(self.strategy, [self.account], predictions, atDateTime, None, 'Director', True, False)

            except Exception as e:
                traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)

                print('eeeee', traceback_str)

                if self.forceSendSlack == True:
                    self.Slack.forceSend('simulations', ':sob: interrupted: ' + traceback_str)

            self.incrementStaticTime()

            if self.tradingBotsEnabled == True:
                self.runStopLossSimulation()

            self.runOn(basedCoin, self.strategyName)

    def runStopLossSimulation(self):
        lastIterationWillBeAt = self.BalancesRepository.staticStartTime
        nextIterationWillBeAt = lastIterationWillBeAt + datetime.timedelta(minutes=- self.predict_every_minutes)

        while nextIterationWillBeAt < lastIterationWillBeAt:
            strategy = self.BalancesRepository.findStrategy(self.strategy['_id'])

            atDateTime = self.BalancesRepository.staticStartTime
            strategyIsLocked = 'lockedUntilDate' in self.strategy and self.strategy['lockedUntilDate'] >= atDateTime

            if strategyIsLocked:
                print('- - - - - - strategy is locked, not continuing with trading bot simulation')
                return

            self.stoploss = StopLossManager(
                self.configurations,
                self.BalancesRepository,
                self.apiClient,
                self.walletClient,
                self.database,
                strategy,
                [self.account]
            )

            self.stoploss.runStopLoss('simulation', None, nextIterationWillBeAt, self.lockStrategyAlsoForStoplossAndJumpToMarket)

            nextIterationWillBeAt = nextIterationWillBeAt + datetime.timedelta(minutes=+ 1)

    def incrementStaticTime(self):
        timeIncrement = self.predict_every_minutes
        lastIterationWasAt = self.BalancesRepository.staticStartTime
        nextIterationWillBeAt = lastIterationWasAt + datetime.timedelta(minutes=+ timeIncrement)
        self.BalancesRepository.staticStartTime = nextIterationWillBeAt

    def preRun(self):

        self.endDatePrices = self.BalancesRepository.retrieveCoinsPriceAtSpecificDatetime(
            self.endDate, self.strategy['baseCoin']
        )

        self.startDatePrices = self.BalancesRepository.retrieveCoinsPriceAtSpecificDatetime(
            self.startingDate, self.strategy['baseCoin']
        )

        self.initial_balance_in_base_coin = 100

        self.startPrice = 1/float(self.startDatePrices[self.firstCoinInStrategy]["p"])
        self.endPrice = 1/float(self.endDatePrices[self.firstCoinInStrategy]["p"])

        self.amountWeStart = round(float(self.initial_balance_in_base_coin) / float(self.startDatePrices[self.firstCoinInStrategy]["p"]), 7)

        increase = self.endPrice - self.startPrice

        self.percentageDifferenceToSurpase = (increase / self.startPrice) * 100

        #### FOR SENDING TO SLACK #####
        #### FOR SENDING TO SLACK #####
        #### FOR SENDING TO SLACK #####

        message = ''

        message += ':fire: '+self.strategyName+' simulation started from ' + str(self.startingDate) + ' until ' + str(self.endDate) + "\n"
        message += ':moneybag: Starting amount: ' + str(self.initial_balance_in_base_coin) + ' ' + self.runOnBaseCoin + ' same as ' + str(self.amountWeStart) + ' ' + self.firstCoinInStrategy + "\n"
        message += ':moneybag: Start price vs end price: ' + str(self.startDatePrices[self.firstCoinInStrategy]["p"]) + ' | ' + str(self.endDatePrices[self.firstCoinInStrategy]["p"]) + "\n"

        if self.tradingBotsEnabled:
            message += ':skull_and_crossbones: '+str(self.firstCoinInStrategy)+' stoploss trailing at ' + str(
                self.stoplossAt) + '%, ' + str(self.strategy['baseCoin']) + ' trailing at ' + str(self.jumpToMarketAt) + '%, take profit at '+ str(self.takeProfitAt) + '%' + "\n"
        else:
            message += ':speak_no_evil: without Stoploss'+ "\n"

        if self.lockStrategyAfterTradingMinutes and self.tradingBotsEnabled:
            message += ':hourglass: Strategy will be locked for ' + str(self.lockStrategyAfterTradingMinutes) + ' minutes if stoploss is triggered' "\n"

        if self.whaleUpPercent and self.tradingBotsEnabled:
            message += ':whale: Whale detector enabled on jumps at ' + str(self.whaleUpPercent) + '%' + "\n"

        if self.whaleDownPercent and self.tradingBotsEnabled:
            message += ':whale: Whale detector enabled on downs at ' + str(self.whaleDownPercent) + '%' + "\n"

        if self.whaleMinuteLookup and self.tradingBotsEnabled:
            message += ':whale2: Whale detector lookup at ' + str(self.whaleMinuteLookup) + ' minutes' + "\n"

        message += ':clock3: Predicts every: ' + str(self.predict_every_minutes) + ' minutes' "\n"

        if self.ignoreStrategyLockOnHardSignal:
            message += ':grey_exclamation: Ignoring strategy lock on hard signal' "\n"

        if self.extendLockUntilHardPrediction:
            message += ':grey_exclamation: Extending lock until hard prediction occurs (buy/sell event)' "\n"

        message += ':art: Collection: ' + str(self.database.tradesCollectionName) + "\n"

        if self.forceSendSlack == True:
            self.Slack.forceSend('simulations', message)

        print(message)

    def afterRun(self):

        # we calculate what do we win from A to B

        self.BalancesRepository.deleteStrategy(self.strategy['_id'])

        accountsContainer = AccountsContainer()
        accountsContainer.addAccount(self.account['accountName'])

        finalBalance = self.BalancesRepository.ourCurrentBalances('simulation', self.strategy['sandboxInitialBalances'], self.BalancesRepository.staticStartTime)

        self.walletClient.unifyBalanceWithExchangeRates(finalBalance, self.BalancesRepository, self.BalancesRepository.staticStartTime, accountsContainer, self.account['accountName'],
                                                        self.firstCoinInStrategy, # TODO Change this
                                                        self.coinsThatStrategyUses,
                                                        self.strategy['baseCoin'])

        finalBtcAmount = self.walletClient.totalBeforeTradingBtc
        finalUsdtAmount = self.walletClient.totalTUSDBeforeTrading

        increase = finalBtcAmount - self.amountWeStart

        finalPercentage = (increase / self.amountWeStart) * 100

        increaseUsdt = finalUsdtAmount - self.initial_balance_in_base_coin
        finalPercentageUsdt = (increaseUsdt / self.initial_balance_in_base_coin) * 100


        #### FOR SENDING TO SLACK #####
        #### FOR SENDING TO SLACK #####
        #### FOR SENDING TO SLACK #####

        csv_file_name = str(self.startingDate) + ' till ' + str(self.endDate) + '_SL_' + str(self.stoplossAt) + '_JTM_' + str(self.jumpToMarketAt) + '_TP_' + str(self.takeProfitAt) + '_sleep_' + str(self.lockStrategyAfterTradingMinutes)

        message = ''

        message += ':zap::zap::zap::zap::zap::zap::zap::zap::zap::zap::zap::zap::zap::zap::zap::zap:' + "\n"
        message += ':zap: '+self.strategyName+' simulation *finished* from ' + str(self.startingDate) + ' until ' + str(self.endDate) + "\n"
        message += ':moneybag: Start price vs end price was: ' + str(self.startDatePrices[self.firstCoinInStrategy]["p"]) + ' | ' + str(self.endDatePrices[self.firstCoinInStrategy]["p"]) + "\n"

        if self.lockStrategyAfterTradingMinutes and self.tradingBotsEnabled:
            message += ':hourglass: Strategy has been locked for ' + str(
                self.lockStrategyAfterTradingMinutes) + ' minutes if stoploss was triggered'

        if self.tradingBotsEnabled:
            message += ':skull_and_crossbones: '+str(self.firstCoinInStrategy)+' stoploss trailing at ' + str(
                self.stoplossAt) + '%, ' + str(self.strategy['baseCoin']) + ' trailing at ' + str(self.jumpToMarketAt) + '%, take profit at '+ str(self.takeProfitAt) + '%' + "\n" + "\n"
        else:
            message += ':speak_no_evil: without Stoploss'+ "\n"+ "\n"

        if self.whaleUpPercent and self.tradingBotsEnabled:
            message += ':whale: Whale detector enabled on jumps at ' + str(self.whaleUpPercent) + '%' + "\n"

        if self.whaleDownPercent and self.tradingBotsEnabled:
            message += ':whale: Whale detector enabled on downs at ' + str(self.whaleDownPercent) + '%' + "\n"

        if self.whaleMinuteLookup and self.tradingBotsEnabled:
            message += ':whale2: Whale detector lookup at ' + str(self.whaleMinuteLookup) + ' minutes' +  "\n"

        message += ':moneybag: Starting amount was: ' + str(self.initial_balance_in_base_coin) + ' ' + self.runOnBaseCoin + ' same as ' + str(self.amountWeStart) + ' '+str(self.firstCoinInStrategy)+'' + "\n"
        message += ':chart_with_upwards_trend: Final balance is: ' + str(finalUsdtAmount) + ' ' + self.runOnBaseCoin + ' same as ' + str(finalBtcAmount) + ' '+str(self.firstCoinInStrategy)+'' + "\n"
        message += ':call_me_hand: ' + str(round(finalPercentage, 2)) + '% '+str(self.firstCoinInStrategy)+' | ' + str(round(finalPercentageUsdt, 2)) + '% ' + str(self.strategy['baseCoin']) + "\n"+ "\n"+ "\n"

        if self.strategyName == 'ploutos':
            message += ':ok_hand: EXPORT COMMAND' + "\n"+  '```mongoexport --host 35.204.239.122:27017 --db aggregated ' \
                       '--collection "'+str(self.database.tradesCollectionName)+'" ' \
                       '--csv --out "'+csv_file_name+'.csv" ' \
                       '--fields "at,totals.ETH,totals.USDT,rates.ETH.p,signals,action"```'
        if self.strategyName == 'procyon':

            message += ':ok_hand: EXPORT COMMAND' + "\n"+  '```mongoexport --host 35.204.239.122:27017 --db aggregated ' \
                       '--collection "'+str(self.database.tradesCollectionName)+'" ' \
                       '--csv --out "'+csv_file_name+'.csv" ' \
                       '--fields "at,totals.BTC,totals.USDT,rates.BTC.p,signals,action"```'

        message += ':clock3: Predicts every: ' + str(self.predict_every_minutes) + ' minutes' "\n"

        if self.ignoreStrategyLockOnHardSignal:
            message += ':grey_exclamation: Ignoring strategy lock on hard signal' "\n"

        if self.extendLockUntilHardPrediction:
            message += ':grey_exclamation: Extending lock until hard prediction occurs (buy/sell event)' "\n"

        message += ':art: Export Collection: "' + str(self.database.tradesCollectionName) + '"' "\n"

        if self.forceSendSlack == True:
            self.Slack.forceSend('simulations', message)

        print(message)

        simulation = Simulation(
            self.strategyId,
            self.startingDate,
            self.endDate,
            {str(self.firstCoinInStrategy) : str(round(finalPercentage, 2)), self.runOnBaseCoin : str(round(finalPercentageUsdt, 2))},
            self.lockStrategyAfterTradingMinutes,
            self.stoplossAt,
            self.jumpToMarketAt,
            self.whaleDownPercent,
            self.whaleUpPercent,
            self.whaleMinuteLookup,
            self.takeProfitAt,
            self.lockStrategyAlsoForStoplossAndJumpToMarket,
            self.tradingBotsEnabled,
            self.predict_every_minutes,
            self.strategyName,
            self.ignoreStrategyLockOnHardSignal,
            self.extendLockUntilHardPrediction,
        )

        self.simulationResultsRepository.aggregateByDateRange(simulation)

        if self.firedFromStudy == True:
            self.BalancesRepository.dropSimulationCollections()
            return finalPercentage

        exit(0)
