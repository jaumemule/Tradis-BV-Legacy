from src.infra.slackClient import Slack
from src.domain.clusterFilter import ClusterFilter
from src.domain.traderManager import TraderManager
from src.application.tradingResultsSerializer import TradingResultsSerializer
from src.application.AccountsContainer import AccountsContainer
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.balancesRepository import BalancesRepository
from src.infra.walletClient import Wallet
from src.infra.ApiClient import ApiClient
import datetime
import time
from src.application.BalanceStateObject import BalanceStateObject

class ProcessManager:

    strategy: None
    openOrdersRetryCounter = 0  # type: int
    Slack = ''
    environmentConfigurations = ''
    Database = ''
    runMethodology = ''

    def __init__(
        self,
            environmentConfigurations: EnvironmentConfigurations,
            BalancesRepository: BalancesRepository,
            walletClient: Wallet,
            apiClient: ApiClient,
            Database: Database
    ) -> None:
        self.environmentConfigurations = environmentConfigurations
        self.BalancesRepository = BalancesRepository
        self.wallet = walletClient
        self.apiClient = apiClient
        self.database = Database

        self.Slack = Slack(
            environmentConfigurations.slackToken,
            environmentConfigurations.environmentName,
            self.environmentConfigurations
        )

    def fire(self,
             strategy: dict,
             accounts: list,
             predictions: list,
             atDateTime,
             exchangeRates = None,
             source = 'Director',
             recordResults = True,
             isStrategyLockedToTrade = True,
             action = 'ml_prediction'
        ) -> None:

        if strategy['runOnMode'] != self.environmentConfigurations.runMethodologySandbox \
                and strategy['runOnMode'] != self.environmentConfigurations.runMethodologyLazySandbox \
                and strategy['runOnMode'] != self.environmentConfigurations.runMethodologyProduction \
                and strategy['runOnMode'] != 'simulation':
            raise ValueError('run mode incorrect ' + strategy['runOnMode'])

        # we replace the predictions to the coins we are. we do not trade at all
        if isStrategyLockedToTrade == True:
            predictions = strategy['currentCoins']

        #TODO this is hacky
        self.runMethodology = strategy['runOnMode']
        self.strategy = strategy # TODO Remove this fleaky states
        self.accounts = accounts # TODO Remove this fleaky states
        self.environmentConfigurations.currentlyRunningMethodology = strategy['runOnMode']

        accountsContainer = AccountsContainer()
        for account in accounts:
            accountsContainer.addAccount(account['accountName'], account)

        # returns a list, example ['NAV', 'XRP', 'RLC', 'BCPT', 'AE']
        # use a maximum of coins to trade
        cluster_filter = ClusterFilter(self.environmentConfigurations)
        coins_to_trade = cluster_filter.fromPredictions(predictions, strategy, self.environmentConfigurations.maximumCoinsToTrade)

        if self.runMethodology == self.environmentConfigurations.runMethodologyProduction:

            # Perform balance lookups:
            accounts_balance_list = self.wallet.ourCurrentBalancesFromExchangeAccountBatch(
                accounts,
                self.strategy['exchange']
            )

        # for sandbox
        else:
            accounts_balance_list = {}
            for account in accounts:

                if self.environmentConfigurations.currentlyRunningMethodology != 'simulation':
                    self.database.connectToAppropiateCollection(account, False, self.environmentConfigurations.currentlyRunningMethodology)

                account_balance = self.BalancesRepository.ourCurrentBalances(self.runMethodology, self.strategy['sandboxInitialBalances'], atDateTime)
                accounts_balance_list[account['accountName']] = account_balance

        exchange_markets = self.strategy['exchangeMarkets']
        trade_manager = TraderManager(self.environmentConfigurations, self.apiClient, self.Slack)

        balances_and_prices_df_dict = {}
        unserialized_tracker_data_dict = {}
        trading_buy_and_sell_lists_dict = {}
        balance_state_object_list_dict = {}

        for accountName, balance in accounts_balance_list.items():

            if 'error' in balance['balances']:
                
                if not accountName:
                    accountName = 'Not known'

                self.Slack.send(':interrobang: Could not fetch balance lookup for account: ' + accountName)
                accountsContainer.addError(accountName, 'could_not_fetch_balance')
                continue

            time_to_search_for_exchange_rates = atDateTime

            if self.environmentConfigurations.currentlyRunningMethodology == 'real_money':
                time_to_search_for_exchange_rates = self.apiClient.time()

            # TODO this is for backwards compatibility on results. remove once procyon is deprecated
            firstCoinInStrategy = [*self.strategy['exchangeMarkets']][0]
            coins_that_strategy_uses = [*self.strategy['exchangeMarkets']]

            # TODO, also exchange rates are retrieved from storage if non existent inside this piece of code.
            # TODO, Should come from an upper layer of the application
            balances_and_prices_df, unserialized_tracker_data = self.wallet.unifyBalanceWithExchangeRates(
                accounts_balance_list[accountName],
                self.BalancesRepository,
                time_to_search_for_exchange_rates,
                accountsContainer,
                accountName,
                firstCoinInStrategy, # TODO we assume only 1 prediction in old strategy results
                coins_that_strategy_uses,
                strategy['baseCoin'],
                exchangeRates,
            )

            # TODO big improvement first step:
            # THIS is meant to replace all the messy calculations around the code and unify it in a single VO
            balance_state_object = BalanceStateObject.from_exchange_rate_and_balance(
                unserialized_tracker_data, # do not forget that exchangeRates can come empty, we take it from above
                balance['balances'],
                strategy,
                accountsContainer.getAccountProperties(accountName),
            )

            balance_state_object_list_dict[accountName] = balance_state_object


            # we extract the markets we gonna use (preconfigured)
            serialised_wallet_state, serialised_tracker_data = trade_manager.generate_trading_input_object(
                coins_to_trade,
                balances_and_prices_df,
                accounts_balance_list[accountName],
                unserialized_tracker_data,
                strategy,
                accountName,
                accountsContainer
            )

            if predictions:

                trading_buy_and_sell_lists = trade_manager.create_trading_df(
                    predictions,
                    serialised_wallet_state,
                    serialised_tracker_data,
                    exchange_markets,
                    accountName,
                    accountsContainer,
                    self.strategy['revertMarket'],
                    self.strategy['baseCoin'],
                )
            else:
                trading_buy_and_sell_lists = {}

            # TODO CHECK IF THIS IS A POTENTIAL BUG
            if len(serialised_wallet_state['new_predictions']) > 0:
                pass
            else:
                trading_buy_and_sell_lists = {}

            balances_and_prices_df_dict[accountName] = balances_and_prices_df
            unserialized_tracker_data_dict[accountName] = unserialized_tracker_data
            trading_buy_and_sell_lists_dict[accountName] = trading_buy_and_sell_lists

        ####            PROCEED ON EXCHANGE OPERATION           ####

        ####            PROCEED ON EXCHANGE OPERATION           ####

        ####         TODO move all this in another file         ####

        ####            PROCEED ON EXCHANGE OPERATION           ####


        sell_orders_in_batches = {}
        buy_orders_in_batches = {}
        sell_orders_response = {}
        buy_orders_response = {}

        if trading_buy_and_sell_lists_dict:

            # here we create a serialization in batches, we do not perform any transaction yet; unless is sandbox
            for accountName, trading_buy_and_sell_lists in trading_buy_and_sell_lists_dict.items():

                transactionMessagesPerAccount = []  # strings

                if accountsContainer.accountHasError(accountName):
                    continue

                if accountName not in trading_buy_and_sell_lists:

                    # self.Slack.send('could not find '+accountName+' in' + str(trading_buy_and_sell_lists))
                    continue

                for transactionPosition, order in trading_buy_and_sell_lists[accountName].items():

                    if 'sell' in order:
                        if order['sell']:
                            sell_orders_request_payload, balances_and_prices_df_dict[accountName], message_on_sell = trade_manager.serialiseSellOrders(
                                balances_and_prices_df_dict[accountName],
                                unserialized_tracker_data_dict[accountName],
                                order['sell'],
                                exchange_markets,
                                accountName,
                                self.strategy['baseCoin']
                            )

                            transactionMessagesPerAccount.append(message_on_sell)

                            sell_orders_in_batches[accountName] = sell_orders_request_payload

                    if 'buy' in order:
                        if order['buy']:
                            buy_orders_request_payload, balances_and_prices_df_dict[accountName], message_on_buy = trade_manager.serialiseBuyOrders(
                                balances_and_prices_df_dict[accountName],
                                unserialized_tracker_data_dict[accountName],
                                order['buy'],
                                exchange_markets,
                                accountName,
                                self.strategy['baseCoin']
                            )

                            transactionMessagesPerAccount.append(message_on_buy)

                            # TODO add this to account container
                            buy_orders_in_batches[accountName] = buy_orders_request_payload

                accountsContainer.addResult(accountName, 'transactionMessages', transactionMessagesPerAccount)

            # if is real money execute exchange order
            if self.runMethodology == self.environmentConfigurations.runMethodologyProduction and isStrategyLockedToTrade == False:

                if sell_orders_in_batches:
                    sell_orders_response = self.wallet.sellInBatches(sell_orders_in_batches, self.strategy['exchange'])

                if buy_orders_in_batches:
                    buy_orders_response = self.wallet.buyInBatches(buy_orders_in_batches, self.strategy['exchange'])


            prediction_state_has_changed = True
            if 'currentCoins' in strategy and action != 'ml_prediction': # trader bot algos should not affect
                prediction_state_has_changed = predictions != strategy['currentCoins']

            slackFancyMessages = []
            lead_account = None
            for account in self.accounts:

                account_name = account['accountName']

                if accountsContainer.accountHasError(account_name):
                    continue

                results_serializer = TradingResultsSerializer()

                if self.environmentConfigurations.currentlyRunningMethodology == 'simulation' or self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox':
                    at = atDateTime
                else:
                    at = datetime.datetime.utcnow()

                sell_orders_statistics = []
                if account_name in sell_orders_in_batches:
                    sell_orders_statistics = sell_orders_in_batches[account_name]

                buy_orders_statistics = []
                if account_name in buy_orders_in_batches:
                    buy_orders_statistics = buy_orders_in_batches[account_name]

                serializer = results_serializer.createResults(
                    sell_orders_statistics,
                    buy_orders_statistics,
                    accountsContainer,
                    account_name,
                    at,
                    source,
                    isStrategyLockedToTrade,
                    self.strategy
                )

                fancyMessage = serializer.convertResultsIntoAfancyMessageString(
                    self.runMethodology,
                    self.strategy['baseCoin'],
                    account_name,
                    source
                )

                if self.environmentConfigurations.currentlyRunningMethodology != 'simulation':
                    self.database.connectToAppropiateCollection(account, False, self.environmentConfigurations.currentlyRunningMethodology)

                if self.environmentConfigurations.currentlyRunningMethodology != 'real_money':
                    self.BalancesRepository.calculateAndSaveSandboxTransaction(
                        balances_and_prices_df_dict[account_name],
                        trading_buy_and_sell_lists_dict[account_name],
                        account_name,
                        atDateTime
                    )

                # assess lead account
                is_lead_account = False
                if 'is_lead' in account:
                    if account['is_lead'] == True:
                        lead_account = account
                        is_lead_account = True

                if recordResults and prediction_state_has_changed:

                    self.BalancesRepository.recordAccountResults(
                        serializer.serialize(
                            account,
                            action,
                            balance_state_object_list_dict[account_name]
                        ),
                        is_lead_account
                    )

                slackFancyMessages.append(fancyMessage)

                del results_serializer

            # TODO generalise this per strategy
            # TODO could happen the first account has an error:
            # TODO so we should continue updating the strategy state anyway
            # pick an account that is always running

            send_slack_message = True

            # no need to proceed if is holding
            if len(self.accounts) > 0 and lead_account != None and prediction_state_has_changed:

                # TODO improve this, is only taking the first of the list but doesn't come in order!
                tradis_account_name = lead_account['accountName']

                if accountsContainer.accountHasError(tradis_account_name) == False:

                    # info: if the main account has traded, mutate some strategy states:
                    # = block immediate trading and reset trailing =
                    # other info:

                    if (tradis_account_name in buy_orders_in_batches and len(buy_orders_in_batches[tradis_account_name]) > 0) \
                            or (tradis_account_name in sell_orders_in_batches and len(sell_orders_in_batches[tradis_account_name]) > 0):

                        # print('----!--- buy orders: ', buy_orders_in_batches)
                        # print('---!---- sell orders: ', sell_orders_in_batches)

                        if isStrategyLockedToTrade == False:
                            self.apiClient.resetTrailing(self.strategy, atDateTime)
                            self.BalancesRepository.updateCurrentCoinsPredictionInStrategy(self.strategy['_id'], predictions)
                            self.BalancesRepository.updateStrategyLastOrdersAtOpenPrice(self.strategy['_id'], predictions, unserialized_tracker_data_dict[tradis_account_name])

                            self.Slack.send(':crescent_moon: Trailings got reset, investment state updated too')

                            if source == 'Stoploss': # only block strategy if stoploss is triggered!

                                if self.environmentConfigurations.currentlyRunningMethodology == 'simulation':
                                    untilTime = atDateTime + datetime.timedelta(minutes=self.strategy['lockingConfigurationInMinutes'])
                                else:
                                    now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
                                    untilTime = now + datetime.timedelta(minutes=self.strategy['lockingConfigurationInMinutes'])  # we store from the previous minute

                                self.Slack.send(':stopwatch: Blocked strategy '+self.strategy['strategyName']+' temporarily after stoploss, until ' + str(untilTime))
                                self.BalancesRepository.lockStrategyTemporarily(self.strategy['_id'], untilTime)

                    elif source == 'Stoploss': # let's not spam slack if no orders are taken but stoploss triggered
                        send_slack_message = False

            messageChunk = ''
            messageCount = 0

            if send_slack_message:
                for message in slackFancyMessages:

                    messageChunk += message + "\n"
                    messageCount += 1

                    if messageCount == 1: # send only one as example
                        messageChunk += '...and ' + str(len(slackFancyMessages)) + ' accounts were processed, in total'
                        self.Slack.send(messageChunk)
                        break

            self.checkIfThereWereAnyTransactionFailures(sell_orders_response)
            self.checkIfThereWereAnyTransactionFailures(buy_orders_response)

        # empty memory
        del exchange_markets
        del trading_buy_and_sell_lists_dict
        del trade_manager
        del accounts_balance_list
        del coins_to_trade
        del cluster_filter
        del predictions
        del balances_and_prices_df_dict
        del unserialized_tracker_data_dict

    def checkIfThereAreOpenOrdersForASingleAccount(self, userAccountName, exchangeName, orders):

        if self.openOrdersRetryCounter > 2:
            self.Slack.send('there are still open orders for ' + userAccountName + ' after several retries')
            # raise Exception('There are still open orders after several retries. Will not proceed on the current flow')

        openOrders = self.wallet.exchangeOpenOrdersSingleAccount(userAccountName, exchangeName, orders)

        if len(openOrders) > 0:
            time.sleep(2)
            self.openOrdersRetryCounter += 1
            self.checkIfThereAreOpenOrdersForASingleAccount(userAccountName, exchangeName, orders)

    def checkIfThereWereAnyTransactionFailures(self, orders) -> None:

        # {'3b391a2b3be3893621554ba3159b5ab7487e609334c8c67c16752a94cc4aeaad_5fcfea7a2f0dc10026a59abf': {'result': [{'BTC/USDT': {'success': False, 'quantity': 0.01378568338, 'error': 'InsufficientFunds', 'message': 'binance Account has insufficient balance for requested action.'}}]}}
        if orders:

            for accountName, order in orders.items():

                order = str(order)

                if 'error' in order:
                    self.Slack.send(':bangbang: Account ' + accountName + ' failed on transaction ' + str(order) + ' shall we disable account manually?... (????)')
                    # self.apiClient.disableAccount(accountName)
                    # found errors:
                    # InsufficientFunds : doesn't probably need a ban
