from src.application.SlackClient import Slack
from src.application.environmentConfigurations import EnvironmentConfigurations
from src.infra.TrackerRepository import TrackerRepository
from src.infra.ApiClient import ApiClient
from src.application.ExchangeRatesCcxtIntegration import ExchangeRatesCcxtIntegration
import pandas as pd
import datetime
from rq import Queue
from redis import Redis
conn = Redis.from_url('redis://redis:6379')
q = Queue(connection=conn)
import time
from src.domain.CouldNotRetrieveTrackerDataException import CouldNotRetrieveTrackerDataException

class Tracker:

    Slack = ''
    environmentConfigurations = ''
    Database = ''
    runMethodology = ''

    def __init__(
        self,
            environmentConfigurations: EnvironmentConfigurations,
            TrackerRepository: TrackerRepository,
            ApiClient: ApiClient,
            Queueing
    ) -> None:
        self.queueing = Queueing
        self.Slack = Slack(
            environmentConfigurations.slackToken,
            environmentConfigurations.environmentName
        )

        self.environmentConfigurations = environmentConfigurations
        self.trackerRepository = TrackerRepository
        self.apiClient = ApiClient

    # track exchange rates per base coin
    def track(self, baseCoin: str = 'BTC', unlockCoins: bool = False) -> None:

        date = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        date -= datetime.timedelta(minutes=1)

        print('capturing...: ', date)

        exchangeRatesLookup = ExchangeRatesCcxtIntegration(self.environmentConfigurations)

        # CAPTURE TUSD FROM BTC/TUSD and revert it

        # RevertCoins = pd.DataFrame([], index=['TUSD'])
        # btcBasedCoin = Binance.requestFromLastRecordAndSerializeData(RevertCoins, date, True, 'BTC')
        # self.trackerRepository.updateOneBtcCollection(
        #     btcBasedCoin, date
        # )

        captureCoinsForUsdtBasedMarket = pd.DataFrame([], index=['BTC', 'ETH'])

        # otherwise some exchanges did not cache yet the new results in some coins and still shows a minute before
        time.sleep(3)

        # TODO make a factory for exchange rates
        # CAPTURE BTC FROM BTC/USDT and save it to USDT collection

        try:
            USDT_exchange_rates = exchangeRatesLookup.requestFromLastRecordAndSerializeData('binance', captureCoinsForUsdtBasedMarket, date, False, 'USDT')
            self.trackerRepository.updateOrInsertBinanceUsdtCollection(
                USDT_exchange_rates, date
            )

            print('captured, triggering queue for binance BTC...')

        except CouldNotRetrieveTrackerDataException as e:
            USDT_exchange_rates = None

            print('did not capture for binance BTC...')

            pass


        self.queueing.enqueueSimpleTask(
            self.queueing.readyToPredict,
            'tracker',
            [str(date), 'binance', 'USDT', USDT_exchange_rates],
            self.queueing.directorQueue
        )

        self.queueing.enqueueSimpleTask(
            self.queueing.triggerStopLoss,
            'tracker',
            [str(date), 'binance', 'USDT', USDT_exchange_rates],
            self.queueing.stoplossQueue
        )

        try:
            # CAPTURE BTC FROM BTC/USDT and save it to USDT collection
            coinbasepro_exchange_rates = exchangeRatesLookup.requestFromLastRecordAndSerializeData('coinbasepro', captureCoinsForUsdtBasedMarket, date, False, 'EUR')
            self.trackerRepository.updateOrInsertCoinbaseproEurCollection(
                coinbasepro_exchange_rates, date
            )

            print('captured, triggering queue for coinbasepro EUR...')
        except CouldNotRetrieveTrackerDataException as e:
            coinbasepro_exchange_rates = None

            print('did not capture for coinbasepro EUR...')

            pass

        # self.queueing.enqueueSimpleTask(
        #     self.queueing.readyToPredict,
        #     'tracker',
        #     [str(date), 'coinbasepro', 'EUR', coinbasepro_exchange_rates],
        #     self.queueing.directorQueue
        # )
        #
        # self.queueing.enqueueSimpleTask(
        #     self.queueing.triggerStopLoss,
        #     'tracker',
        #     [str(date), 'coinbasepro', 'EUR', coinbasepro_exchange_rates],
        #     self.queueing.stoplossQueue
        # )

        # self.queueing.emptyQueue('director')
        # self.queueing.emptyQueue('stoploss')
