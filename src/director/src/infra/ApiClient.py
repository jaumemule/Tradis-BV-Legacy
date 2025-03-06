import requests
import json
import datetime

class ApiClient:

    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations
        self.url = environmentConfigurations.walletUrl
        self.apiClientUrl = environmentConfigurations.apiClientUrl
        self.headers = {"client-secret": environmentConfigurations.walletSecret,
                        "client-id": environmentConfigurations.walletId,
                        'Content-type': 'application/json', 'Accept': 'text/plain'}

    def retrieveSoftLockedCoins(self):
        r = requests.get(self.apiClientUrl + '/coins/soft-lock', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not retrieve the coins')

        return r.json()

    def strategy(self, strategyName):

        r = requests.get(self.apiClientUrl + '/strategies/'+strategyName, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Strategy ' + strategyName + ' not found')

        return r.json()

    def accountsByStrategy(self, strategyId):

        r = requests.get(self.apiClientUrl + '/accounts/'+strategyId, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Strategy ' + strategyId + ' not found or no accounts related')

        return r.json()

    def strategies(self):
        r = requests.get(self.apiClientUrl + '/strategies', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Could not retrieve strategies')

        return r.json()

    def unactiveStrategy(self, strategyName):

        data = json.dumps({"active": False})

        r = requests.patch(self.apiClientUrl + '/strategies/' + strategyName, data=data, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Director could not unactive strategy')

    def time(self):

        r = requests.get(self.apiClientUrl + '/time', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Could not retrieve strategies')

        response = r.json()

        return response['utc']

    def softLockCoinPerStrategy(self, coin, coinPrice, stoppedAtLossPercentage, strategy):

        body = {'checkedAtPrice': coinPrice, 'strategy' : strategy, 'stoppedAtLossPercentage' : stoppedAtLossPercentage}

        data = json.dumps(body)
        r = requests.post(self.apiClientUrl + '/coins/soft-lock/' + coin, data=data, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not soft lock')

        return r.json()

    def softUnlockCoin(self, coin):
        r = requests.delete(self.apiClientUrl + '/coins/soft-lock/'+coin, headers=self.headers)
        if r.status_code not in range(200, 399) :
            raise ValueError('Tracker could not soft lock')

    def retrieveCoins(self):
        r = requests.get(self.apiClientUrl + '/coins', headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Tracker could not retrieve the coins')

        return r.json()

    def updateStrategyMarketCoinStopLossTrailingPrice(self, strategy, coinToUpdate, trailing):

        if not 'trailings' in strategy:
            strategy['trailings'] = {}

        coinsInTrailing = strategy['trailings']

        if not coinToUpdate in coinsInTrailing:
            coinsInTrailing[coinToUpdate] = {}

        coinsInTrailing[coinToUpdate]['trailingPrice'] = trailing
        coinsInTrailing[coinToUpdate]['updatedAt'] = str(datetime.datetime.utcnow())

        data = json.dumps({"trailings": coinsInTrailing})

        r = requests.patch(self.apiClientUrl + '/strategies/' + strategy['strategyName'], data=data, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Director could not update trailings')

    def updateStrategyMarketCoinJumpToMarketTrailingPrice(self, strategy, coinToUpdate, trailing):

        if not 'trailings' in strategy:
            strategy['trailings'] = {}

        coinsInTrailing = strategy['trailings']

        if coinToUpdate not in coinsInTrailing:
            coinsInTrailing[coinToUpdate] = {}

        coinsInTrailing[coinToUpdate]['trailingJumpToMarketPrice'] = trailing
        coinsInTrailing[coinToUpdate]['updatedAt'] = str(datetime.datetime.utcnow())

        data = json.dumps({"trailings": coinsInTrailing})

        r = requests.patch(self.apiClientUrl + '/strategies/' + strategy['strategyName'], data=data, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Director could not update trailings')

    def resetTrailing(self, strategy, at):

        if not 'trailings' in strategy:
            strategy['trailings'] = {}

        coinsInTrailing = strategy['trailings']

        for coinToUpdate, information in coinsInTrailing.items():
            coinsInTrailing[coinToUpdate]['trailingPrice'] = 0
            coinsInTrailing[coinToUpdate]['trailingJumpToMarketPrice'] = 0
            coinsInTrailing[coinToUpdate]['updatedAt'] = str(at)

        data = json.dumps({"trailings": coinsInTrailing})

        r = requests.patch(self.apiClientUrl + '/strategies/' + strategy['strategyName'], data=data, headers=self.headers)

        print('---->>>> trailings got reset', str(coinsInTrailing))

        if r.status_code != 200:
            raise ValueError('Director could not reset trailing')

    def disableAccount(self, accountName) -> None:

        data = json.dumps({})

        r = requests.patch(self.apiClientUrl + '/disable-account/' + accountName, data=data, headers=self.headers)

        if r.status_code != 200:
            raise ValueError('Could not disable account')
