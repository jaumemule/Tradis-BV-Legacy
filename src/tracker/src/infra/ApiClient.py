import requests
import json
import datetime
from pandas.io.json import json_normalize

class ApiClient:

    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations
        self.apiClientUrl = environmentConfigurations.apiClientUrl
        self.internalWalletUrl = environmentConfigurations.internalWalletUrl
        self.headers = {"client-secret": environmentConfigurations.ApiSecret,
                        "client-id": environmentConfigurations.ApiId,
                        'Content-type': 'application/json', 'Accept': 'text/plain'}

    def retrieveStrategies(self):
        r = requests.get(self.apiClientUrl + '/strategies', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not retrieve the strategies')

        return r.json()

    def strategy(self, strategyName):
        r = requests.get(self.apiClientUrl + '/strategies/'+strategyName, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Strategy ' + strategyName + ' not found')

        return r.json()

    def retrieveCoins(self):
        r = requests.get(self.apiClientUrl + '/coins', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not retrieve the coins')

        return r.json()

    def retrieveSoftLockedCoins(self):
        r = requests.get(self.apiClientUrl + '/coins/soft-lock', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not retrieve the coins')

        return r.json()

    def softLockCoinPerStrategy(self, coin, coinPrice, stoppedAtLossPercentage, strategy):

        body = {'checkedAtPrice': coinPrice, 'strategy' : strategy, 'stoppedAtLossPercentage' : stoppedAtLossPercentage}

        data = json.dumps(body)
        r = requests.post(self.apiClientUrl + '/coins/soft-lock/' + coin, data=data, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not soft lock')

        return r.json()

    # TODO this is a duplicate from director. source of truth should be there until we move stop loss to director
    def retrieveLastGlobalDataFromSomeMinutesBefore(self, minutes):

        date = datetime.datetime.utcnow() - datetime.timedelta(
            minutes=minutes + 5 # request a bigger range, in case there is data missing
        )

        dataFrom = datetime.datetime.strftime(date, "%Y-%m-%dT%H:%M")

        r = requests.get(self.apiClientUrl + '/aggregations/BTC', params={"after": dataFrom}, headers=self.headers)
        data = r.json()

        # debug
        # for minute in data:
        #     print(minute['date'])

        return data[len(data) - minutes - 1] # would return the last 5 minutes of data

    def softUnlockCoin(self, coin):
        r = requests.delete(self.apiClientUrl + '/coins/soft-lock/'+coin, headers=self.headers)
        if r.status_code not in range(200, 399) :
            raise ValueError('Tracker could not soft lock')

    # TODO this is a duplicate from director. source of truth should be there until we move stop loss to director
    def ourCurrentBalancesFromExchange(self, exchange):

        r = requests.get(self.internalWalletUrl + '/wallet/balances', headers=self.headers)
        balancesFromWallet = r.json()

        r = requests.get(self.internalWalletUrl + '/coins', headers=self.headers)
        coinsFromWallet = r.json()

        coinsList = []
        for coin in coinsFromWallet:
            coinsList.append(coin['coin'])

        # backwards compatible with sandbox
        balances = balancesFromWallet[exchange]['result']['total']

        balancesInUse = {}
        for coin, balance in balances.items():
            if coin in coinsList:
                balancesInUse[coin] = balance

        # filter the coins we are using
        finalBalances = {}
        finalBalances['date'] = datetime.datetime.now()
        finalBalances['balances'] = balancesInUse

        return finalBalances

    # TODO this is a duplicate from director. source of truth should be there until we move stop loss to director
    def sellFromExchange(self, body, exchange):

        data = json.dumps(body)

        r = requests.post(self.internalWalletUrl + '/wallet/sell', data=data, headers=self.headers)

        if r.status_code != 200:
            raise Exception('We could not sell! some error happened')

        payload = r.json()

        # TODO bugfix check empty binance without result (must be an error)
        exchangeResponse = payload[exchange]['result']

        results = [list(a.values())[0]["success"] for a in exchangeResponse]

        if not any(results):
            raise Exception('We could not sell! Due some transaction error: ' + str(exchangeResponse))
