import datetime
from src.application.SlackClient import Slack
from src.domain.CouldNotRetrieveTrackerDataException import CouldNotRetrieveTrackerDataException
import ccxt
from time import sleep
import traceback

class ExchangeRatesCcxtIntegration:
    def __init__(self, environmentConfigurations) -> None:
        self.slack = Slack(
            environmentConfigurations.slackToken,
            environmentConfigurations.environmentName
        )

    def load_exchange_markets_with_retry_mechanism(self, exchangeConnection, exchangeName, retryCounter = 0):
        if retryCounter <= 2:
            try:
                exchangeConnection.load_markets()
                return exchangeConnection
            except Exception as e:

                traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)

                print(traceback_str)

                retryCounter += 1

                self.slack.send('I could not retrieve markets from: ' + str(exchangeName) + ', retry number: ' + str(retryCounter))

                sleep(5)

                # create a new connection for fallback
                del exchangeConnection
                exchangeConnection = self.exchange_connection_factory(exchangeName)

                self.load_exchange_markets_with_retry_mechanism(exchangeConnection, exchangeName, retryCounter)

        else:
            self.slack.send('I failed on loading exchange markets ' + exchangeName)
            raise CouldNotRetrieveTrackerDataException('I failed on loading exchange markets ' + exchangeName)

    def load_exchange_rate_with_retry_mechanism(self, exchangeConnection, exchangeName, market, retryCounter = 0):
        if retryCounter <= 2:
            try:
                return exchangeConnection.fetch_ohlcv(market, '1m', limit=2)
            except Exception as e:

                traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)

                print(traceback_str)

                retryCounter += 1

                sleep(1)
                self.load_exchange_rate_with_retry_mechanism(exchangeConnection, exchangeName, market, retryCounter)

        else:
            self.slack.send('I failed on loading exchange rates after 3 retries for: ' + exchangeName)
            raise CouldNotRetrieveTrackerDataException('I failed on loading exchange rates for ' + exchangeName)

    def exchange_connection_factory(self, exchangeName):
        # create a module
        factory = {
            'binance': ccxt.binance({
                'enableRateLimit': True,
            }),

            'coinbasepro': ccxt.coinbasepro(),
        }

        return factory.get(exchangeName, lambda: "Invalid Exchange")

    def requestFromLastRecordAndSerializeData(self, exchangeName: str, coinsToTrack, now, revertMarket = False, baseCoin ='BTC'):

        exchangeConnection = self.exchange_connection_factory(exchangeName)

        exchangeConnection = self.load_exchange_markets_with_retry_mechanism(exchangeConnection, exchangeName)

        aggregation = {"date": now}

        maxDateTolerance = now + datetime.timedelta(minutes =- 75) # we do not want a coin outdated in time!

        market = ''
        for coin in coinsToTrack.index:

            try:
                market = coin + '/' + baseCoin

                if revertMarket:
                    market = baseCoin + '/' + coin

                item = self.load_exchange_rate_with_retry_mechanism(exchangeConnection, exchangeName, market)
                # item = exchangeConnection.fetch_ohlcv(market, '1m', limit=2)

                item = item[len(item) - 2] # previous minute item

                coinDate = datetime.datetime.fromtimestamp(item[0] / 1000.0)

                if coinDate < maxDateTolerance:
                    self.slack.send('Date too low for coin ' + coin + ', did not capture')
                    continue

                #### HISTORY OF THE RESPONSE ####
                # [
                #     1504541580000, // UTC timestamp in milliseconds, integer
                #     4235.4, // (O)pen price, float
                #     4240.6, // (H)ighest price, float
                #     4230.0, // (L)owest price, float
                #     4230.7, // (C)losing price, float
                #     37.72941911 // (V)olume( in terms of the base currency), float
                # ],

                open = float(item[1])
                high = float(item[2])
                originalHigh = float(item[2])
                low = float(item[3])
                price = float(item[4])
                volume = float(item[5])

                # in case we capture a coin from a different base market
                if revertMarket == True:
                    open = round(1 / open, 15)
                    high = round(1 / low, 15)
                    low = round(1 / originalHigh, 15)
                    volume = round(volume * price, 15)
                    price = round(1 / price, 15)

                aggregation[coin] = {}
                aggregation[coin]['o'] = str(open)
                aggregation[coin]['h'] = str(high)
                aggregation[coin]['l'] = str(low)
                aggregation[coin]['p'] = str(price)
                aggregation[coin]['v'] = str(volume)

            except KeyError as e:
                error = ":bangbang: Could not retrieve the market info " + market + " from " + exchangeName
                self.slack.send(error)

            except Exception as e:
                raise CouldNotRetrieveTrackerDataException('unknown error')

        if len(aggregation) == 0:
            raise CouldNotRetrieveTrackerDataException('there are no results')

        del exchangeConnection

        return aggregation
