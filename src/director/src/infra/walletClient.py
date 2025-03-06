import datetime
import requests
import json
from src.infra.slackClient import Slack
import pandas as pd

class Wallet:

    url = ''
    lengthOfPredictionDataInMinutes = ''
    extraLenOfPredictionsToPreventMissingData = 30
    totalUSDTBeforeTrading = 0
    totalBeforeTradingBtc = 0
    currentBnbMarketValue = 0
    currentUSDMarketValue = 0
    currentBtcMarketValue = 0
    totalBnbBeforeTrading = 0
    totalTUSDBeforeTrading = 0

    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations
        self.url = environmentConfigurations.walletUrl
        self.internalWalletUrl = environmentConfigurations.internalWalletUrl
        self.lengthOfPredictionDataInMinutes = environmentConfigurations.lengthOfPredictionDataInMinutes
        self.apiAuth = {"client-secret": environmentConfigurations.walletSecret,
                        "client-id": environmentConfigurations.walletId,
                        'Content-type': 'application/json', 'Accept': 'text/plain'}

        self.persistedData = False
        self.lastTimeItLoadedAChunckOfData = datetime.datetime.now()

        self.slack = Slack(
            environmentConfigurations.slackToken,
            environmentConfigurations.environmentName,
            self.environmentConfigurations
        )

    # TODO move this to another repository
    def unifyBalanceWithExchangeRates(
            self,
            accountBalance,
            balancesRepository,
            timeNow,
            accountsContainer,
            accountName,
            coinToRetrieve,
            coins_that_strategy_uses: list,
            base_coin='BTC',
            exchangeRates=None
    ) -> object:

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        if not exchangeRates:
            # if self.environmentConfigurations.currentlyRunningMethodology == 'simulation' or self.environmentConfigurations.currentlyRunningMethodology == 'lazy_sandbox':
            #     tracker = balancesRepository.retrieveCoinsPriceAtSpecificDatetime(
            #         balancesRepository.staticStartTime, base_coin
            #     )
            #
            # else:
            #     timeNow = timeNow[:-8]
            #     tracker = balancesRepository.retrieveCoinsPriceAtSpecificDatetime(
            #         datetime.datetime.strptime(str(timeNow), '%Y-%m-%dT%H:%M'), base_coin
            #     )

            serialized_datetime = timeNow
            if self.environmentConfigurations.currentlyRunningMethodology == 'real_money':
                timeNow = timeNow[:-8]
                serialized_datetime = datetime.datetime.strptime(str(timeNow), '%Y-%m-%dT%H:%M')

            # print('---<<<<0--->>> time now ', timeNow, serialized_datetime)

            tracker = balancesRepository.retrieveCoinsPriceAtSpecificDatetime(
                serialized_datetime, base_coin
            )
        else:
            tracker = exchangeRates
            tracker[base_coin] = {'p': 1}  # Add extra for reference currency

            # cast to float (store floats instead?)
            for key, item in tracker.items():
                if (key != 'date' and key != '_id'):
                    for k, i in item.items():
                        tracker[key][k] = float(i)

        exchange_rates_to_use = {}
        for coin in coins_that_strategy_uses:
            exchange_rates_to_use[coin] = tracker[coin]

        # We create a dataframe that will store the current balances, both in amount and in BTC
        balances_df = pd.DataFrame(0, index=accountBalance["balances"].keys(), columns=["balances", "trade"])

        # In the following loop we check the balances of every coin and the price of every coin in BTC
        # TODO: vectorize this
        for index, coin in enumerate(accountBalance["balances"]):

            # Here we check for balances
            balances_df.loc[coin, "balances"] = list(accountBalance["balances"].values())[index]

            # Here we check for trading rate to btc at the moment (the try-catch is in case there are missings in our data)
            try:
                balances_df.loc[coin, "trade"] = exchange_rates_to_use[coin]["p"]
            except:
                pass

        # We multiply row balances with userAccountList to btc to have all amounts in BTC
        balances_df["btc_balance"] = balances_df["balances"].astype(float) * balances_df["trade"].astype(float)
        # We order the balances to get the five highest (in BTC)
        balances_df.sort_values(by="btc_balance", axis=0, ascending=False, inplace=True)

        # @TODO we don't need this now, but would be nice to track
        # we should extract this loggers
        total_balance_in_base_coin = balances_df["btc_balance"].sum()

        # TODO this is deprecation
        if base_coin == 'BTC':
            if 'TUSD' in tracker:
                totalTUSDBeforeTrading = round(float(total_balance_in_base_coin) / float(exchange_rates_to_use["TUSD"]["p"]), 2)
                accountsContainer.addResult(accountName, 'totalTUSDBeforeTrading', totalTUSDBeforeTrading)
                accountsContainer.addResult(accountName, 'currentUSDMarketValue', exchange_rates_to_use["TUSD"]["p"])
                accountsContainer.addResult(accountName, 'totalBeforeTradingBtc', total_balance_in_base_coin)

        if base_coin in fallbackCoins:
            if base_coin in tracker:
                # TODO this is deprecation
                print('exchange_rates_to_use --- ', exchange_rates_to_use)
                totalBeforeTradingBtc = round(float(total_balance_in_base_coin) / float(exchange_rates_to_use[coinToRetrieve]["p"]), 7)
                accountsContainer.addResult(accountName, 'totalTUSDBeforeTrading', total_balance_in_base_coin)
                accountsContainer.addResult(accountName, 'currentUSDMarketValue', exchange_rates_to_use[base_coin]["p"])
                accountsContainer.addResult(accountName, 'totalBeforeTradingBtc', totalBeforeTradingBtc)

                # READ ONLY FOR SIMULATIONS *TO IMPROVE*
                self.totalBeforeTradingBtc = totalBeforeTradingBtc
                self.totalTUSDBeforeTrading = total_balance_in_base_coin

        if coinToRetrieve in exchange_rates_to_use:
            # TODO this is deprecation
            accountsContainer.addResult(accountName, 'currentBtcMarketValue', exchange_rates_to_use[coinToRetrieve]['p'])

        return balances_df, exchange_rates_to_use

    def ourCurrentBalancesFromExchangeAccountBatch(self, userAccountsList, exchangeName):

        payload = []

        for accounts in userAccountsList:
            chunk = {
                "exchangeName" : exchangeName,
                "account" : accounts['accountName'],
            }

            payload.append(chunk)

        data = json.dumps(payload)

        r = requests.post(self.internalWalletUrl + '/wallet/balances', data=data, headers=self.apiAuth)

        if r.status_code != 200:
            raise Exception('We could not check balance! some error happened')

        balancesFromWallet = r.json()

        r = requests.get(self.internalWalletUrl + '/coins', headers=self.apiAuth)
        coinsFromWallet = r.json()

        coinsList = []
        for coin in coinsFromWallet:
            coinsList.append(coin['coin'])

        accounts = {}

        date = datetime.datetime.now()
        for accountName, wallet in balancesFromWallet.items():

            accounts[accountName] = {}

            if 'result' not in wallet:
                accounts[accountName]['date'] = date
                accounts[accountName]['balances'] = {'error': 'could_not_fetch'} # this is for process manager
                continue

            if wallet['result'] is None:
                accounts[accountName]['date'] = date
                accounts[accountName]['balances'] = {'error': 'could_not_fetch'} # this is for process manager
                continue

            balances = wallet['result']['total']
            accounts[accountName]['date'] = date
            accounts[accountName]['balances'] = {}

            for coin, balance in balances.items():
                if coin in coinsList and coin not in self.environmentConfigurations.ignoreCoinsInBalance:
                    accounts[accountName]['balances'][coin] = balance

        return accounts

    def exchangeOpenOrdersSingleAccount(self, userAccountName, exchangeName, orders):

        if len(orders[userAccountName]) == 0:
            return []

        orders = orders[userAccountName]
        markets = []

        for order in orders:
            market = order['baseCurrency'] + '/' + order['targetCurrency']
            markets.append({'market': market})

        payload = [
            {
                "exchangeName" : exchangeName,
                "account" : userAccountName,
                "orders" : markets
            }
        ]

        data = json.dumps(payload)

        r = requests.post(self.internalWalletUrl + '/wallet/open-orders', data=data, headers=self.apiAuth)
        openOrders = r.json()

        if r.status_code != 200:
            raise Exception('We could not buy! some error happened ' + str(openOrders))

        return openOrders[userAccountName]['result']


    def buySingleOrder(self, orders, accountName, exchangeName):

        payload = [
            {
                "exchangeName" : exchangeName,
                "account" : accountName,
                "orders" : orders[accountName]
            }
        ]

        data = json.dumps(payload)

        r = requests.post(self.internalWalletUrl + '/wallet/buy', data=data, headers=self.apiAuth)

        payload = r.json()

        if r.status_code != 200:
            raise Exception('We could not buy! some error happened ' + str(payload))

        exchangeResponse = payload[accountName]['result']

        results = [list(a.values())[0]["success"] for a in exchangeResponse]

        if not any(results):
            raise Exception('We could not buy! Due some transaction error: ' + str(payload))


    def sellSingleOrder(self, orders, accountName, exchangeName):

        payload = [
            {
                "exchangeName" : exchangeName,
                "account" : accountName,
                "orders" : orders[accountName]
            }
        ]

        print(payload)

        data = json.dumps(payload)

        r = requests.post(self.internalWalletUrl + '/wallet/sell', data=data, headers=self.apiAuth)

        payload = r.json()

        if r.status_code != 200:
            raise Exception('We could not sell! some error happened ' + str(payload))

        exchangeResponse = payload[accountName]['result']

        results = [list(a.values())[0]["success"] for a in exchangeResponse]

        if not any(results):
            raise Exception('We could not sell! Due some transaction error: ' + str(payload))


    def sellInBatches(self, ordersPerAccount: dict, exchangeName) -> object:

        payload = []

        for accountName, sellOrder in ordersPerAccount.items():

            if sellOrder[accountName]:  # might come empty!
                order = {
                    "exchangeName" : exchangeName,
                    "account" : accountName,
                    "orders" : sellOrder[accountName]
                }

                payload.append(order)

        data = json.dumps(payload)

        response = {}

        if data:

            r = requests.post(self.internalWalletUrl + '/wallet/sell', data=data, headers=self.apiAuth)

            response = r.json()

            print('SELL RESPONSE', response)

            if r.status_code != 200:
                raise Exception('We could not sell! some error happened ' + str(response))

        return response

    def buyInBatches(self, ordersPerAccount: dict, exchangeName) -> dict:

        payload = []

        for accountName, buyOrder in ordersPerAccount.items():

            if buyOrder[accountName]:  # might come empty!
                order = {
                    "exchangeName" : exchangeName,
                    "account" : accountName,
                    "orders" : buyOrder[accountName]
                }

                payload.append(order)

        data = json.dumps(payload)

        response = {}

        if data:
            r = requests.post(self.internalWalletUrl + '/wallet/buy', data=data, headers=self.apiAuth)

            response = r.json()

            print('BUY RESPONSE', response)

            if r.status_code != 200:
                raise Exception('We could not buy! some error happened ' + str(response))

        return response
