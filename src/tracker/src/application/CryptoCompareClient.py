import datetime
import requests
from src.application.SlackClient import Slack
from src.domain.CouldNotRetrieveTrackerDataException import CouldNotRetrieveTrackerDataException


class CryptoCompareClient:
    def __init__(self, environmentConfigurations) -> None:
        self.slack = Slack(
            environmentConfigurations.slackToken,
            environmentConfigurations.environmentName
        )

    def requestFromLastRecordAndSerializeData(self, coinsToTrack, baseCoin):

        index = list(coinsToTrack.index)
        maximum = 60
        steps = round(len(index) / maximum)

        # the maximum and steps shenanigans are because the server only allows for
        # 60 simultanious coin exchanges
        timing = datetime.datetime.utcnow()
        aggregateList = {"date": timing};

        for i in range(steps + 1):

            scoin = ",".join(list(index)[maximum * i:maximum * (i + 1)])
            url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms={}' \
                .format(scoin, baseCoin)

            try:
                page = requests.get(url, timeout=120)
                data = page.json()

                for element in data['RAW']:
                    aggregateList[element] = {"p": 0, "v": 0}
                    aggregateList[element]['p'] = data['RAW'][element][baseCoin]['PRICE']
                    aggregateList[element]['v'] = data['RAW'][element][baseCoin]['VOLUME24HOUR']

            except Exception as e:
                print(e)
                raise CouldNotRetrieveTrackerDataException('')

        return aggregateList
