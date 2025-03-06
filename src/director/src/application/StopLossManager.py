from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.ApiClient import ApiClient
from src.infra.balancesRepository import BalancesRepository
from src.domain.StopLoss import StopLoss
import datetime
from src.infra.slackClient import Slack
from src.infra.walletClient import Wallet
from src.application.AccountsContainer import AccountsContainer

class StopLossManager:

    Slack = ''
    environmentConfigurations = ''
    runMethodology = ''

    def __init__(
        self,
            environmentConfigurations: EnvironmentConfigurations,
            BalancesRepository: BalancesRepository,
            ApiClient: ApiClient,
            walletClient: Wallet,
            database,
            strategy: dict,
            accounts: list
    ) -> None:
        self.Slack = Slack(
            environmentConfigurations.slackToken,
            environmentConfigurations.environmentName,
            environmentConfigurations
        )

        self.environmentConfigurations = environmentConfigurations
        self.balancesRepository = BalancesRepository
        self.apiClient = ApiClient
        self.wallet = walletClient
        self.strategy = strategy
        self.database = database
        self.unlockCoins = False
        self.accounts = accounts

    def runStopLoss(self, runMethod, exchangeRates = None, presetRunDateTime = False, lockTradingIfStrategyIsLocked = False, recordResultsPerIteration = True) -> None:

        #TODO this is hacky, remove this states. is also deprecated
        self.runMethodology = runMethod
        self.environmentConfigurations.currentlyRunningMethodology = runMethod

        accountsContainer = AccountsContainer()
        for account in self.accounts:
            accountsContainer.addAccount(account['accountName'], account)

        if not presetRunDateTime:
            timeNow = self.apiClient.time()
            timeNow = timeNow[:-8]
            runAt = datetime.datetime.strptime(str(timeNow), '%Y-%m-%dT%H:%M')
        else:
            timeNow = presetRunDateTime
            runAt = datetime.datetime.strptime(str(timeNow), '%Y-%m-%d %H:%M:%S')

        if not exchangeRates:
            # print('I do not have exchange rates from queue, checking db')

            try:
                exchangeRates = self.balancesRepository.retrieveCoinsPriceAtSpecificDatetime(
                    runAt,
                    self.strategy['baseCoin']
                )
            except Exception as e:
                self.Slack.send('!!!!!! Could not fetch exchange rates. aborting stoploss')
                return

        else:
            # TODO remove this patch
            # cast to float (store floats instead?)
            for key, item in exchangeRates.items():
                if (key != 'date' and key != '_id'):
                    for k, i in item.items():
                        exchangeRates[key][k] = float(i)

            exchangeRates[self.strategy['baseCoin']] = {'p': 1}  # Add extra for reference currency

        stop_loss = StopLoss(
            self.environmentConfigurations,
            self.balancesRepository,
            self.Slack,
            self.apiClient,
            self.wallet,
            self.database,
            self.strategy
        )

        coinsInStrategy = [*self.strategy['exchangeMarkets']]

        coinsInStrategyWithoutBaseCoin = list(set(coinsInStrategy))
        coinsInStrategyWithoutBaseCoin.remove(self.strategy['baseCoin'])

        # update strategy state
        stop_loss.updateTrailings(exchangeRates, coinsInStrategyWithoutBaseCoin)

        # retrieve strategy (we could keep it in memory for performance)
        strategy = self.balancesRepository.findStrategy(self.strategy['_id'])

        ## TODO this is a mess! instantiating object again bcs strategy state has changed
        stop_loss = StopLoss(
            self.environmentConfigurations,
            self.balancesRepository,
            self.Slack,
            self.apiClient,
            self.wallet,
            self.database,
            strategy
        )

        actualHour = runAt.hour
        actualMinute = runAt.minute

        runAtHours = [actualHour]  # run every hour if not set
        if 'runAtHours' in strategy:
            runAtHours = strategy['runAtHours']

        if actualMinute in strategy['runAtMinutes'] and actualHour in runAtHours:
            return

        if lockTradingIfStrategyIsLocked and 'lockedUntilDate' in strategy:

            locked_until_datetime = strategy['lockedUntilDate']

            if not isinstance(strategy['lockedUntilDate'], datetime.datetime):
                locked_until_datetime = strategy['lockedUntilDate'][:-8]
                locked_until_datetime = datetime.datetime.strptime(locked_until_datetime, '%Y-%m-%dT%H:%M')

            # is a date object
            if locked_until_datetime >= runAt:
                return

        percentageOfLossPerInvestedCoinPerStrategy = stop_loss.calculateStopLossPerInvestedCoinPerStrategy(
            exchangeRates, runAt
        )

        # percentageOfLossPerInvestedCoinPerStrategy=[{'poc_work': [{'coin': 'BTC', 'percentageOfLoss': 0, 'checkedAtPrice': 3.11e-06, 'strategy': 'poc_work', 'runOnMode': 'sandbox', 'stopTrading': True}]}]

        if len(percentageOfLossPerInvestedCoinPerStrategy) == 0:
            return

        # TODO refactor this weird structure (old)
        # we only want to pass 1 coin for now, we might change this in the future
        # percentageOfLossPerInvestedCoinPerStrategy = percentageOfLossPerInvestedCoinPerStrategy[0][self.strategy['strategyName']][0]

        for coinToCheck in percentageOfLossPerInvestedCoinPerStrategy[0][self.strategy['strategyName']]:

            # stopExecution is for preventing buying and selling on the same iteration to the base coin
            stopExecution = stop_loss.calculateAndSellStopLossCoins(
                strategy,
                self.accounts,
                accountsContainer,
                coinToCheck,
                exchangeRates,
                timeNow,
                coinsInStrategyWithoutBaseCoin,
                recordResultsPerIteration
            )

            if stopExecution == True:
                break

        del exchangeRates
