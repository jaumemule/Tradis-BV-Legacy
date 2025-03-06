import numpy as np
import pandas as pd
import datetime
from pandas.io.json import json_normalize
from src.application.dataAnalyzer import DataAnalyzer
from src.domain.tradingIndicators import TradingIndicators


class GeneralizedDataProvider:
    analyzer = None
    norm_period = 15
    volume_indices = ['v', 'qv', 't', 'tbv', 'tqv']

    def __init__(self, BalancesRepository, coin_list, indices_list, runAt, slackClient, cfg):

        self.now = runAt
        self.balancesRepository = BalancesRepository
        self.slackClient = slackClient
        self.coin_list = coin_list
        self.indices_list = indices_list

        self.indicators = TradingIndicators(cfg)
        self.max_indicator_period = self.indicators.get_max_indicator()

    def mock_data_analyzer(self):
        findDate = self.now
        untilBackup = findDate + datetime.timedelta(minutes=-100)
        self.analyzer = DataAnalyzer(start_date=untilBackup,
                                     end_date=findDate,
                                     slack_client=self.slackClient,
                                     verbose=False
                                     )

    def _reverse(self, candle_df):
        price_coins = []
        for col in candle_df.columns:
            # First we do the price indices, which we just need to invert
            if col.split(".")[1] not in self.volume_indices:
                price_coins.append(col)
                candle_df[col] = 1 / candle_df[col]
        # This is kind of ugly because the price indicators need to be done last
        #  so that we already have the new typical price
        for col in candle_df.columns:
            # Then we do the volume indices, which have to be divided by new
            #  price (or tipical prices, which is more robust)
            if col.split(".")[1] in self.volume_indices:
                candle_df[col] = candle_df[col] / candle_df[price_coins].mean(axis=1)

        return candle_df

    def retrieve_data(self, candles, forecast_len, time_frame=300, base_coin='USDT', reverse=False):

        # If candle size is not 1, we need to work a little here. The price-related
        # indices stay the same, but the volume related indices need to be summed over
        # the candle size. Therefore, in the retrieval phase, we need to differentiate
        # between the two. What we could do is to take minutely data over the whole
        # timeframe and then compute volumes and discard the left over minutes. But this
        # is going to be quite slow and very RAM demanding, so what we will do is to
        # make a petition for each index of each coin and treat them separately and put
        # them together in the end.

        self.forecast_len = forecast_len
        self.time_frame = time_frame
        self.candles = candles
        # Generate the coin/index mixed list (i.e., we have [TUSD] and [.p, .v], create
        # [TUSD.p, TUSD.v]
        retrieve_list = []
        for coin in self.coin_list:
            retrieve_list.append([coin + '.' + x for x in self.indices_list])
        retrieve_list = [item for sublist in retrieve_list for item in sublist]

        # Now we do the petitions to the database.
        # We start by finding the timeframes we want to work on; keep in mind that we
        # need to retrieve more data than the window we will work on because we need to
        # compute the indicators (hence the self.indicator_periods term). We also need
        # one extra candle to compute the volumes up to the first time point
        findDate = self.now

        df = None
        for candle_size in candles:

            jump_size = max(self.forecast_len, candle_size)
            left_overs = self.max_indicator_period + self.norm_period
            back_time = candle_size + (jump_size * (time_frame + left_overs))
            untilBackup = findDate + datetime.timedelta(minutes=-int(back_time))

            # We have two types, the price type and the volume type, which we
            # will treat separately:
            verbose = True
            candle_df = None
            for coin_index in retrieve_list:
                data = self.balancesRepository.retrieve_data_by_one_indicator_and_period_of_time(
                    untilBackup,
                    findDate,
                    coin_index,
                    base_coin
                )

                index_df = json_normalize(data)

                self.analyzer = DataAnalyzer(start_date=untilBackup,
                                             end_date=findDate,
                                             slack_client=self.slackClient,
                                             verbose=verbose
                                             )
                index_df, verbose = self.analyzer.analyze(index_df, verbose)

                # close (price)
                if coin_index.split('.')[1] == 'p':
                    index_df = index_df
                # open
                elif coin_index.split('.')[1] == 'o':
                    index_df = index_df.shift(candle_size - 1)
                # high
                elif coin_index.split('.')[1] == 'h':
                    index_df = index_df.rolling(candle_size).max()
                # low
                elif coin_index.split('.')[1] == 'l':
                    index_df = index_df.rolling(candle_size).min()
                # volumes
                elif coin_index.split('.')[1] in self.volume_indices:
                    index_df = index_df.rolling(candle_size).sum()
                else:
                    raise ValueError("I don't understand the indices. Aborting.")

                # Join them together
                candle_df = index_df if candle_df is None else candle_df.join(index_df)

            # Remove the missings created at the beginning
            candle_df = candle_df.iloc[candle_size:, :]

            # If we are oriented to making trading coin (eg BTC), we need to reverse the
            #  indices, so as to maximize the inverses
            if reverse:
                candle_df = self._reverse(candle_df)

            # Compute the trading indicators
            candle_df = self._compute_indicators(candle_df, candle_size)

            # rename columns
            candle_df.columns = [f"{a}_{candle_size}" for a in candle_df.columns]

            df = candle_df if df is None else df.join(candle_df)

        return df

    def _compute_indicators(self, col_df, candle):
        # This is a complex part; we need to cut the whole dataframe in pieces that
        # we will use to compute the trading indicators. If the candle is smaller
        # than the forecast length, this is easy, just cut by candles and compute.
        # The problem arises when the candle size is bigger than the forecast length.
        # In this case, we need to compute the trading indicators more often than the
        # candle sizes, so we can't cut the dataframe first and we need to do it in
        # pieces and then put them together.

        if candle <= self.forecast_len:
            # Easy case
            col_df = col_df.iloc[::-candle, :].iloc[::-1, :]

            # compute the indicators
            col_df = self.indicators.compute_indicators(col_df)
            step_ = int(self.forecast_len / candle)
            col_df = col_df.iloc[::-step_, :].iloc[::-1, :]
            col_df.index = pd.to_datetime(col_df.index).round('1s')
            return col_df

        else:
            # Smaller forecast than candle case
            # Prepare the output df
            output_df = pd.DataFrame()
            # Check how many forecast lengths inside one candle:
            ratio = int(candle / self.forecast_len)
            # Turn the col_df around so that my head doesn't explode
            col_df = col_df.iloc[::-1]
            # Instantiate indicator class
            indicators = self.indicators

            for i in range(ratio):
                # Pick the candle sized chunks shifted a forecast_len from origin
                partial_df = col_df.iloc[i * self.forecast_len::candle, :].iloc[::-1]
                partial_df = indicators.compute_indicators(partial_df)
                output_df = pd.concat([output_df, partial_df], axis=0)

            # Reorder by datetime
            output_df.index = pd.to_datetime(output_df.index).round('1s')
            return output_df.sort_index(axis=0)

    def rolling_normalization(self, df):

        # apply rolling normalization we are using the element we are normalizing to
        # compute mean and std; this is more comfortable code-wise, but maybe it
        # should be changed (TODO: think about this)
        #  Update: trials with and without RN look much better when it is used
        def norm_(x):
            return (x - x.rolling(self.norm_period).mean()) / \
                   (x.rolling(self.norm_period).std(ddof=0))

        df = df.apply(norm_, axis=0)

        # clean infs and missings
        df = df.replace([np.inf, -np.inf], np.nan).ffill().bfill()

        # remove first n_period entries, which will make no sense
        return df.iloc[self.norm_period:, ]

    @staticmethod
    def to_float(df):
        return df.astype(np.float64)

    @staticmethod
    def missing_data_check(df):
        assert df.isnull().sum().sum() == 0, \
            'There are missing values in data. Aborting'

    def analyze_non_reals(self, df):
        self.analyzer.analyze_non_reals(df)

    def data_shape_correction(self, df):
        return df.iloc[-self.time_frame:, :]
