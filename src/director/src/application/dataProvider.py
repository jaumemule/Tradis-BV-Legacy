import numpy as np
import datetime
from pandas.io.json import json_normalize
from src.application.dataAnalyzer import DataAnalyzer


class DataProvider:
    analyzer = None
    volume_indices = ['v', 'qv', 't', 'tbv', 'tqv']

    def __init__(self, BalancesRepository, coin_list, indices_list, runAt, slackClient, mlEnvConfigs):

        self.now = runAt
        self.balancesRepository = BalancesRepository
        self.slackClient = slackClient

        self.out_list = ['rsi', 'bandwidth', 'percent-b', 'cv', 'x', 'chop']
        self.period = mlEnvConfigs['indicators']['period']
        self.chop_period = mlEnvConfigs['indicators']['chop_period']
        self.rsi_period = mlEnvConfigs['indicators']['rsi_period']
        period_list_max = mlEnvConfigs['indicators']['period_list_max']
        self.period_list = list(range(1, period_list_max))
        self.indicator_periods = max(self.period, self.rsi_period, self.chop_period,
                                     period_list_max)
        self.volumes_indicators = ['v', 'qv', 't', 'tbv', 'tqv']
        self.coin_list = coin_list
        self.indices_list = indices_list
        self.window = mlEnvConfigs['about_data']['window']
        self.num_coins_ = 1  # TODO: move outside
        self.coins = [mlEnvConfigs['financial']['trading_coin']]

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

    def retrieve_data(self, time_frame=300, candle_size=1, base_coin='USDT', reverse=False):

        # If candle size is not 1, we need to work a little here. The price-related indices stay the same, but the
        # volume related indices need to be summed over the candle size. Therefore, in the retrieval phase, we need
        # to differentiate between the two. What we could do is to take minutely data over the whole timeframe and then
        # compute volumes and discard the left over minutes. But this is going to be quite slow and very RAM demanding,
        # so what we will do is to make a petition for each index of each coin and treat them separately and put them
        # together in the end.
        # TODO: review this; optimize it; find mongo queries that allow us to retrieve a value every candle_size time.

        self.time_frame = time_frame

        # Generate the coin/index mixed list (i.e., we have [TUSD] and [.p, .v], create [TUSD.p, TUSD.v]
        retrieve_list = []
        for coin in self.coin_list:
            retrieve_list.append([coin + '.' + x for x in self.indices_list])
        retrieve_list = [item for sublist in retrieve_list for item in sublist]

        # Now we do the petitions to the database.
        # We start by finding the timeframes we want to work on; keep in mind that we need to retrieve more data than
        # the window we will work on because we need to compute the indicators (hence the self.indicator_periods term)
        # We also need one extra candle to compute the volumes up to the first time point
        findDate = self.now
        back_time = (time_frame + self.indicator_periods + 1) * candle_size
        untilBackup = findDate + datetime.timedelta(minutes=-int(back_time))

        # We have two types, the price type and the volume type, which we
        # will treat separately:
        verbose = True
        df = None
        for coin_index in retrieve_list:
            data = self.balancesRepository.retrieve_data_by_one_indicator_and_period_of_time(
                untilBackup,
                findDate,
                coin_index,
                base_coin
            )

            coin_df = json_normalize(data)

            self.analyzer = DataAnalyzer(start_date=untilBackup,
                                         end_date=findDate,
                                         slack_client=self.slackClient,
                                         verbose=verbose
                                         )
            coin_df, verbose = self.analyzer.analyze(coin_df, verbose)

            final_index = coin_df.index[::-candle_size]

            # close (or price) (it's important that it is the first to preserve date indices)
            if coin_index.split('.')[1] == 'p':
                coin_df = coin_df.iloc[::-candle_size, :]
            # open
            elif coin_index.split('.')[1] == 'o':
                coin_df = coin_df.iloc[-candle_size::-candle_size, :]
            # high
            elif coin_index.split('.')[1] == 'h':
                coin_df = coin_df.rolling(candle_size).max().iloc[::-candle_size, :]
            # low
            elif coin_index.split('.')[1] == 'l':
                coin_df = coin_df.rolling(candle_size).min().iloc[::-candle_size, :]
            # volumes
            elif coin_index.split('.')[1] in self.volumes_indicators:
                coin_df = coin_df.rolling(candle_size).sum().iloc[::-candle_size, :]
            else:
                raise ValueError("I don't understand the indices. Aborting.")

            coin_df.set_index(final_index, inplace=True)

            df = coin_df if df is None else df.join(coin_df)

        if reverse:
            df = self._reverse(df)

        return df.iloc[::-1, :].transpose()

    @staticmethod
    def to_float(df):
        return df.astype(np.float64)

    @staticmethod
    def missing_data_check(df):
        assert df.isnull().sum().sum() == 0, 'There are missing values in data. Aborting'

    def analyze_non_reals(self, df):
        self.analyzer.analyze_non_reals(df)

    @staticmethod
    def standardize(row):
        return (row[0] - row[1]) / (row[2] - row[1])

    def compute_indicators_one_coin(self, df):

        # typical price (tp) calculation
        try:
            df['tp'] = df[['p', 'h', 'l']].apply(lambda x: (x[0] + x[1] + x[2]) / 3,
                                                 axis=1)
        except KeyError:
            "We are missing indices to compute the indicators. Aborting."

        # rate of change (roc) calculation for several periods
        for i, per in enumerate(self.period_list):
            df['roc-' + str(i)] = df['tp'].pct_change(per)
            df['roc-' + str(i)] = df['roc-' + str(i)].interpolate(
                method='linear').bfill()

        # Bollinger bands bandwidth and percent-b calculations
        df['std'] = df['tp'].rolling(self.period).std()
        df['min'] = df['tp'].rolling(self.period).min()
        df['max'] = df['tp'].rolling(self.period).max()

        df['std'] = df['std'].interpolate(method='linear').bfill()
        df['min'] = df['min'].interpolate(method='linear').bfill()
        df['max'] = df['max'].interpolate(method='linear').bfill()

        df['ewm-tp'] = df['tp'].ewm(span=self.period, min_periods=0, adjust=False,
                                    ignore_na=False).mean()

        df['lower'] = df[['ewm-tp', 'std']].apply(lambda x: x[0] - 2 * x[1], axis=1)
        df['upper'] = df[['ewm-tp', 'std']].apply(lambda x: x[0] + 2 * x[1], axis=1)

        df['bandwidth'] = df[['ewm-tp', 'lower', 'upper']].apply(
            lambda x: (x[2] - x[1]) / x[0], axis=1)
        df['percent-b'] = df[['tp', 'lower', 'upper']].apply(
            lambda x: self.standardize(x), axis=1)

        # coefficient of variation (cv) calculation
        df['cv'] = df[['ewm-tp', 'std']].apply(lambda x: x[1] / x[0], axis=1)

        # average true range calculation
        df['close-p'] = df['p'].shift(1)
        df['close-p'] = df['close-p'].interpolate(method='linear').bfill()

        df['tr'] = df[['close-p', 'h', 'l']].apply(
            lambda x: max([(x[1] - x[2]), abs(x[1] - x[0]), abs(x[2] - x[0])]),

            axis=1)
        df['atr'] = df['tr'].ewm(span=1, min_periods=0, adjust=False,
                                 ignore_na=False).mean()
        df['atr-sum'] = df['atr'].rolling(self.chop_period).sum()
        df['atr-sum'] = df['atr-sum'].interpolate(method='linear').bfill()

        df['max-high'] = df['h'].rolling(self.chop_period).max()
        df['min-low'] = df['l'].rolling(self.chop_period).min()

        df['max-high'] = df['max-high'].interpolate(method='linear').bfill()
        df['min-low'] = df['min-low'].interpolate(method='linear').bfill()

        # choppiness index calculation
        df['chop'] = df[['atr-sum', 'max-high', 'min-low']].apply(
            lambda x: np.log10(x[0] / (x[1] - x[2])) / np.log10

            (self.chop_period), axis=1)
        df['chop'] = df['chop'].interpolate(method='linear').bfill()

        # x indicator calculation
        df['x'] = df[['p', 'o']].apply(lambda x: (2 * x[0] - x[1]) / x[0], axis=1)

        # rsi calculation
        df['diff-c'] = df[['p']].diff()
        df['diff-c'] = df['diff-c'].interpolate(method='linear').bfill()
        df['up'] = df[['diff-c']].apply(lambda x: x[0] if x[0] > 0 else 0, axis=1)
        df['down'] = df[['diff-c']].apply(lambda x: -x[0] if x[0] < 0 else 0, axis=1)
        df['roll-up'] = df['up'].ewm(span=self.rsi_period, min_periods=0, adjust=False,
                                     ignore_na=False).mean()
        df['roll-down'] = df['down'].ewm(span=self.rsi_period, min_periods=0,
                                         adjust=False, ignore_na=False).mean()
        eps = 1e-10
        df['rsi'] = df[['roll-up', 'roll-down']].apply(
            lambda x: 1.0 - 1.0 / (1.0 + x[0] / (x[1] + eps)), axis=1)

        return df

    def compute_all_indicators(self, df):
        df = df.transpose()
        new_df = None
        for coin in self.coin_list:
            column_names = [coin + str('.') + a for a in self.indices_list]

            coin_df = df.loc[:, column_names]
            coin_df.columns = [a.split('.')[1] for a in coin_df.columns]
            coin_df = self.compute_indicators_one_coin(coin_df)
            coin_df.columns = [coin + '.' + a for a in coin_df.columns]

            new_df = coin_df if new_df is None else new_df.join(coin_df)

        return new_df.transpose()

    def data_shape_correction(self, df):
        return df.iloc[:, -self.time_frame:]

    def get_feature_names(self):
        out = self.out_list.copy()
        for i, j in enumerate(self.period_list):
            out.append('roc-' + str(i))
        return out
