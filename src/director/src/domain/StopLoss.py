from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.domain.traderManager import TraderManager
import pandas as pd
from bson.objectid import ObjectId
import datetime
from src.application.ProcessManager import ProcessManager
from src.infra.Queueing import Queueing
from src.application.BalanceStateObject import BalanceStateObject

class StopLoss:

    def __init__(
        self,
            environmentConfigurations: EnvironmentConfigurations,
            balancesRepository,
            Slack,
            apiClient,
            walletClient,
            database,
            strategy
    ) -> None:
        self.environmentConfigurations = environmentConfigurations
        self.balancesRepository = balancesRepository
        self.Slack = Slack
        self.apiClient = apiClient
        self.wallet = walletClient
        self.database = database
        self.strategy = strategy
        self.queueing = Queueing(environmentConfigurations)

    def shouldTakeProfit(self, profitAtPercentage: float, calculatedPercentage: float) -> bool:
        if not profitAtPercentage or profitAtPercentage == 0:
            return False

        return calculatedPercentage >= profitAtPercentage # 0 >= 5

    def shouldStopTrading(self, stopAtLossPercentage: float, calculatedPercentage: float) -> bool:

        if not stopAtLossPercentage or stopAtLossPercentage == 0:
            return False

        if stopAtLossPercentage > 0:
            stopAtLossPercentage *= -1

        return calculatedPercentage <= stopAtLossPercentage # 0 <= -5

    def shouldJumpToMarket(self, jumpToMarketPercentage: float, calculatedPercentage: float) -> bool:
        if not jumpToMarketPercentage or jumpToMarketPercentage == 0:
            return False

        return calculatedPercentage >= jumpToMarketPercentage # 0 >= 5

    def calculatePercentageOfDifference(self, actualPrice: float, trailing: float) -> float:

        difference = (float(actualPrice) - float(trailing)) / float(actualPrice) * 100

        # print(' trailing: ', trailing, 'price:', actualPrice, ' difference:', difference, 'type: ',type)

        # exception: if trailing was set to 0 we do not compute
        if trailing == 0:
            difference = 0

        return difference

    # 2 booleans
    def shouldItTriggerWhaleDetector(self, price, coin, runAt, threshold_down=2, threshold_up=2, minutes_lookup=3):
        minutes_ago = runAt - datetime.timedelta(minutes=minutes_lookup)

        try:
            price_three_minutes_ago = self.balancesRepository.retrieveCoinsPriceAtSpecificDatetime(
                minutes_ago,
                self.strategy['baseCoin']
            )[coin]['p']
        except Exception:
            # Idempotency, but would be nice to log it
            return False, False

        percentage_increase = ((price - price_three_minutes_ago) / price) * 100

        is_whale_selling = percentage_increase < (threshold_down * -1)
        is_whale_buying = percentage_increase > threshold_up

        if is_whale_selling or is_whale_buying:
            print('!!! Whale detector ~~~ ',percentage_increase, is_whale_selling, is_whale_buying)

        return is_whale_selling, is_whale_buying

    def calculateStopLossPerInvestedCoinPerStrategy(self, trackedData, runAt) -> list:

        percentageOfDifferencePerCoin = []

        strategy = self.strategy

        if not strategy['active']:
            return []

        if 'trailings' in strategy:

            # TODO we assume the coins that trailings contains are the same as the market coins we use.
            # That's a wrong assumption that needs to be iterated.
            for coin, information in strategy['trailings'].items():

                if coin not in trackedData:
                    continue

                # we do not check the base coin, jump to market is in market coins
                if coin in self.strategy['baseCoin']:
                    continue

                price = trackedData[coin]["p"]
                trailingStopLoss = information['trailingPrice']
                trailingJumpToMarket = information['trailingJumpToMarketPrice']

                # we do not check base coin, that would mean jump to market later
                if coin == self.strategy['baseCoin']:
                    continue

                if 'currentCoins' not in self.strategy:
                    self.Slack.send('No currentCoins defined to calculate stoploss or jump to market :(')
                    continue

                percentageOfDifferenceForStopLoss = 0
                percentageOfDifferenceForJumpToMarket = 0
                percentageOfDifferenceSinceBuyOrder = 0
                is_whale_selling = False
                is_whale_buying = False

                # if config for whale detector
                if 'whaleDownPercent' in strategy['trailingsPercentageConfig'] and 'whaleUpPercent' in strategy['trailingsPercentageConfig']:
                    is_whale_selling, is_whale_buying = self.shouldItTriggerWhaleDetector(
                        price, coin, runAt, strategy['trailingsPercentageConfig']["whaleDownPercent"],
                        strategy['trailingsPercentageConfig']["whaleUpPercent"],
                        strategy['trailingsPercentageConfig']["whaleMinuteLookup"]
                    )

                # TODO improve this FIAT check to include all of those we use
                if 'USDT' in self.strategy['currentCoins']: # we are in FIAT, so we check if we jump to bitcoin

                    percentageOfDifferenceForJumpToMarket = self.calculatePercentageOfDifference(
                        price,
                        trailingJumpToMarket,
                    )

                else: # we calculate if to move to FIAT
                    percentageOfDifferenceForStopLoss = self.calculatePercentageOfDifference(
                        price,
                        trailingStopLoss,
                    )

                    # TODO disabled take profit, too much hassle for now
                    # if 'lastOrders' in self.strategy: # we need to know at what price was the last buy
                    #     percentageOfDifferenceSinceBuyOrder = self.calculatePercentageOfDifference(
                    #         price,
                    #         self.strategy['lastOrders'][coin],
                    #     )
                    # else:
                    #     percentageOfDifferenceSinceBuyOrder = 0
                    #     print('ERROR: No lastOrders defined to calculate take profit :(')

                percentageOfDifferencePerCoin.append(
                    {
                        'coin' : coin,
                        'percentageOfDifferenceForStopLoss': percentageOfDifferenceForStopLoss,
                        'isWhaleBuying': is_whale_buying,
                        'isWhaleSelling': is_whale_selling,
                        'percentageOfDifferenceForJumpToMarket': percentageOfDifferenceForJumpToMarket,
                        'percentageOfDifferenceForTakeProfit': percentageOfDifferenceSinceBuyOrder,
                        'checkedAtPrice': trackedData[coin]["p"],
                        'strategy': strategy['strategyName'],
                        'exchangeMarkets': strategy['exchangeMarkets'],
                        'baseCoin': strategy['baseCoin'],
                        'runOnMode': strategy['runOnMode']
                    }
                )

                # print('trailings %: ', percentageOfDifferenceForStopLoss, percentageOfDifferenceForJumpToMarket)
                # print('coin we are: ', self.strategy['currentCoins'])

        # TODO do trailings config per coin?
        for index, percentageOfPriceDifference in enumerate(percentageOfDifferencePerCoin):

            percentageOfDifferencePerCoin[index]['stopTrading'] = self.shouldStopTrading(
                self.strategy['trailingsPercentageConfig']['stopLoss'],
                percentageOfPriceDifference['percentageOfDifferenceForStopLoss']
            ) or percentageOfPriceDifference['isWhaleSelling']

            percentageOfDifferencePerCoin[index]['jumpToMarket'] = self.shouldJumpToMarket(
                self.strategy['trailingsPercentageConfig']['jumpToMarket'],
                percentageOfPriceDifference['percentageOfDifferenceForJumpToMarket']
            ) or percentageOfPriceDifference['isWhaleBuying']

            percentageOfDifferencePerCoin[index]['takeProfit'] = self.shouldTakeProfit(
                self.strategy['trailingsPercentageConfig']['takeProfit'],
                percentageOfPriceDifference['percentageOfDifferenceForTakeProfit']
            )

        aggregate = [v["strategy"] for v in percentageOfDifferencePerCoin]
        finalDictionary = []
        for element in set(aggregate):
            finalDictionary.append({element: [v for v in percentageOfDifferencePerCoin if v["strategy"] == element]})

        return finalDictionary

    # ASSUMPTION THAT BASE COIN IS USDT!!!!!
    def calculateAndSellStopLossCoins(
            self,
            strategy,
            accounts,
            accountsContainer,
            percentageOfLossPerInvestedCoinInStrategy,
            exchangeRates: dict,
            timeNow,
            coinsInStrategyWithoutBaseCoin,
            recordResultsPerIteration = True
    ):

        process: ProcessManager = ProcessManager(
            self.environmentConfigurations,
            self.balancesRepository,
            self.wallet,
            self.apiClient,
            self.database
        )

        runIndate = timeNow

        predictions = []

        action = None

        coinToTrade = coinsInStrategyWithoutBaseCoin[0]

        naming = ''
        if percentageOfLossPerInvestedCoinInStrategy['stopTrading'] == True:
            predictions = [self.strategy['baseCoin']]
            action = 'stopTrading'
            naming = 'Stoploss'
            percentage = str(percentageOfLossPerInvestedCoinInStrategy['percentageOfDifferenceForStopLoss'])

        if percentageOfLossPerInvestedCoinInStrategy['takeProfit'] == True:
            predictions = [self.strategy['baseCoin']]
            action = 'takeProfit'
            naming = 'Take profit'
            percentage = str(percentageOfLossPerInvestedCoinInStrategy['percentageOfDifferenceForTakeProfit'])

        if percentageOfLossPerInvestedCoinInStrategy['jumpToMarket'] == True:

            if action != 'stopTrading': # to not to sell and buy
                # TODO to define how to jump to market with different coins
                predictions = [coinToTrade] # take first coin to jump, do not partition per coin yet
                action = 'jumpToMarket'
                naming = 'Jump to market'
                percentage = str(percentageOfLossPerInvestedCoinInStrategy['percentageOfDifferenceForJumpToMarket'])
            else:
                self.Slack.send('stoploss and jump to market coalition' + str(percentageOfLossPerInvestedCoinInStrategy))

        processAccounts = []
        accountsByBatch = []

        if len(predictions) > 0:

            if self.environmentConfigurations.currentlyRunningMethodology == 'simulation':
                # print('--1--', action, percentage, predictions, coinsInStrategyWithoutBaseCoin, strategy)
                process.fire(strategy, accounts, predictions, runIndate, exchangeRates, 'Stoploss', True, False, action)

                # print(self.strategy['strategyName'], str(percentageOfLossPerInvestedCoinInStrategy['percentageOfDifferenceForStopLoss']))

                self.Slack.send(':fire: '+naming+' got triggered at ' + str(runIndate) + ' for ' + self.strategy['strategyName']
                                + ' at % ' +percentage
                                + ', might not trade if accounts are already in base coin\n\n')

                # self.apiClient.resetTrailing(self.strategy, runIndate)
            else: # then enqueue
                for account in accounts:

                    if account['active'] == True:
                        processAccounts.append(account)

                        if len(processAccounts) >= 20:  # process in batches of 20

                            accountsByBatch.append(processAccounts)
                            processAccounts = []

                # append the last ones
                if len(processAccounts) > 0:
                    accountsByBatch.append(processAccounts)

                for accounts in accountsByBatch:
                    # TODO order of args is important. create a VO and an specific job or method

                    self.queueing.enqueueSimpleTask(
                        self.queueing.processAccounts,
                        'Stoploss',
                        [
                            runIndate,
                            strategy,
                            predictions,
                            exchangeRates,
                            accounts,
                            False
                        ],
                        self.queueing.directorQueue
                    )

            # if 'lockingConfigurationInMinutes' in strategy and strategy['lockingConfigurationInMinutes']:
            #     print('!locking strategy!')
            #     untilTime = timeNow + datetime.timedelta(minutes=strategy['lockingConfigurationInMinutes'])
            #     self.balancesRepository.lockStrategyTemporarily(strategy['_id'], untilTime)
            #     self.apiClient.resetTrailing(self.strategy) # might happen we are already in the same coin, so we reset trailings

        ### EXTRA FOR SIMULATIONS ####
        ### EXTRA FOR SIMULATIONS ####
        ### EXTRA FOR SIMULATIONS ####

        # if is not zero would be created in process manager, just for statistics
        # we just store more detailed data on hold per minute

        if recordResultsPerIteration == False:
            return

        if self.environmentConfigurations.currentlyRunningMethodology == 'simulation' and len(predictions) == 0:

            accounts_balance_list = {}
            for account in accounts:

                if self.environmentConfigurations.currentlyRunningMethodology != 'simulation':
                    self.database.connectToAppropiateCollection(account, False, 'simulation')

                account_balance = self.balancesRepository.ourCurrentBalances('simulation', self.strategy['sandboxInitialBalances'], timeNow)
                accounts_balance_list[account['accountName']] = account_balance

            for account in accounts:

                account_name = account['accountName']
                balance = accounts_balance_list[account_name]
                # for accountName, balance in accounts_balance_list.items():

                if len(balance) == 0:
                    continue

                account = accountsContainer.getAccountProperties(account_name)

                # TODO big improvement first step:
                # THIS is meant to replace all the messy calculations around the code and unify it in a single VO
                balance_state_object = BalanceStateObject.from_exchange_rate_and_balance(
                    exchangeRates,  # do not forget that exchangeRates can come empty, we take it from above
                    balance['balances'],
                    strategy,
                    account,
                )

                # TODO This is to keep the backwards compatiblity with the director, refactor
                # We create a dataframe that will store the current balances, both in amount and in BTC
                balances_df = pd.DataFrame(0, index=balance["balances"].keys(),
                                           columns=["balances", "trade"])

                # In the following loop we check the balances of every coin and the price of every coin in BTC
                for index, coin in enumerate(balance["balances"]):

                    # Here we check for balances
                    balances_df.loc[coin, "balances"] = list(balance["balances"].values())[index]

                    # Here we check for trading rate to btc at the moment (the try-catch is in case there are missings in our data)
                    try:
                        balances_df.loc[coin, "trade"] = exchangeRates[coin]["p"]
                    except:
                        continue

                # We multiply row balances with userAccountList to btc to have all amounts in BTC
                balances_df["btc_balance"] = balances_df["balances"].astype(float) * balances_df["trade"].astype(float)
                # We order the balances to get the five highest (in BTC)
                balances_df.sort_values(by="btc_balance", axis=0, ascending=False, inplace=True)

                sell = {}

                balanceConvertedInUsdt = balance["balances"][strategy['baseCoin']]
                minimum_to_trade_in_dollars = self.environmentConfigurations.minimAmountToTradeInDollars

                # trick for simulations
                if balanceConvertedInUsdt < minimum_to_trade_in_dollars:
                    movedToCoinName = coinToTrade
                else:
                    movedToCoinName = self.strategy['baseCoin']
                # end of trick

                balanceConvertedInUsdt = balances_df["btc_balance"].sum()
                balanceConvertedInBtc = round(float(balanceConvertedInUsdt) / float(exchangeRates[coinToTrade]["p"]), 7)
                message = 'hold'

                usdtPrice = exchangeRates[strategy['baseCoin']]["p"]

                self._recordTrade(
                    timeNow,
                    account,
                    balanceConvertedInUsdt,
                    balanceConvertedInBtc,  # TODO swap cases if the base coin is not USDT
                    usdtPrice,
                    exchangeRates[coinToTrade]["p"],
                    movedToCoinName,
                    message,
                    balance_state_object
                )

        return

    def _recordTrade(self, at, account, totalUSDBeforeTrading, totalBtcBeforeTrading, USDvalue, BTCvalue, prediction, message, balance_state_object):

        # TODO this should use the serialiser of director
        result = {
            '_account': ObjectId(account['_id']),
            'bought': None,
            'sold': None,
            'at': at,
            'totalBtcBeforeTrading': totalBtcBeforeTrading,
            'totalUSDBeforeTrading': totalUSDBeforeTrading,
            'totalBnbBeforeTrading': None,
            'USDvalue': USDvalue,
            'BNBvalue': 0,
            'BTCvalue': BTCvalue,
            'transactionMessages': message,
            'source': 'Stoploss',
            'action': message,
            'AIpredictions': [prediction],
            'repeatedPredictionsRegardingPreviousOne': None,
            'traderIntendedToBuy': None,
            'traderIntendedToSell': None,
            'previousInvestmentWithCurrentCoinValue': None,
            'predictedCoinsWithCurrentCoinValue': None,
            'previousCoinsWithMoney': None,

            # new release
            'balances': balance_state_object.get_balances(),
            'rates': balance_state_object.get_rates(),
            'totals': balance_state_object.get_totals(),
            'signals': [prediction],
            'exchange': self.strategy['exchange'],
            '_strategy': balance_state_object.get_strategy_id(),
            '_user': balance_state_object.get_user_id(),

        }

        # assess lead account
        is_lead_account = False
        if 'is_lead' in account:
            if account['is_lead'] == True:
                is_lead_account = True

        self.balancesRepository.recordAccountResults(result, is_lead_account)

        pass

    def unlockCoinsIfNecessary(self, softLockedCoins, oldDataMinuteToCalculateUnlock, trackedDataList):

        for lockedCoin in softLockedCoins:
            actualCoinPrice = trackedDataList[lockedCoin['coin']]['p']
            oldCoinPrice = oldDataMinuteToCalculateUnlock[lockedCoin['coin']]['p']

            shouldUnlock, percentage = self.shouldUnlockCoins(actualCoinPrice, oldCoinPrice)
            if shouldUnlock:
                self.apiClient.softUnlockCoin(lockedCoin['coin'])
                self.Slack.send(':aaw_yeah: ' + lockedCoin['coin'] + ' was unlocked for every strategy! '
                                + 'at percentage +' + str(round(percentage, 2)) + '%'
                                + ', actual price is: ' + str(actualCoinPrice)
                                + ' and 5 min ago (' + str(oldDataMinuteToCalculateUnlock['date']) + ') was: ' + str(oldCoinPrice))

                # TODO sent to statistics

    def shouldUnlockCoins(self, actualCoinPrice, oldCoinPrice):

        minPercentageToUnlock = 0.5

        up = (actualCoinPrice - oldCoinPrice) / oldCoinPrice * 100
        # print('coin at percentage', up)

        #  did not go up enough
        if up < 0:
            up = 0

        return up > minPercentageToUnlock, up

    def updateTrailings(self, trackedDataList, coinsInStrategyWithoutBaseCoin: list):

        fallbackCoins = self.environmentConfigurations.fallbackCoins
        strategy = self.strategy

        # we need this to initialise for the first time
        missingCoins = []

        if not 'trailings' in strategy:
            trailings = {}
        else:
            trailings = strategy['trailings']

        for coin in coinsInStrategyWithoutBaseCoin:

            if coin not in trackedDataList:
                print('MISSING COIN IN STOPLOSS ---->', coin, trackedDataList['date'])
                continue

            if coin not in trailings:
                missingCoins.append(coin)
                continue

            # to invert BTC price
            coinPrice = trackedDataList[coin]['p']

            calculated_coin_price = self._calculate_coin_price_for_jump_to_market(coin, coinPrice, fallbackCoins, trackedDataList)

            # principal rule
            if ((float(calculated_coin_price) > float(trailings[coin]['trailingPrice']))
                    or trailings[coin]['trailingPrice'] == 0
            ):
                self.apiClient.updateStrategyMarketCoinStopLossTrailingPrice(self.strategy, coin, calculated_coin_price)

            # principal rule
            if ((float(calculated_coin_price) < float(trailings[coin]['trailingJumpToMarketPrice']))
                    or trailings[coin]['trailingJumpToMarketPrice'] == 0
            ):
                self.apiClient.updateStrategyMarketCoinJumpToMarketTrailingPrice(self.strategy, coin, calculated_coin_price)

    def _calculate_coin_price_for_jump_to_market(self, coin, coinPrice, fallbackCoins, trackedDataList):

        if self.strategy['revertMarket'] and self.strategy['baseCoin'] == 'BTC':
            tusdPrice = trackedDataList['TUSD']['p']
            coinPrice = 1 / float(tusdPrice)

        return coinPrice



