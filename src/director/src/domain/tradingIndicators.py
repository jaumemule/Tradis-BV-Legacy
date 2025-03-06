# Compute the trading indicators

import numpy as np
from talib._ta_lib import MACD, ADOSC


class TradingIndicators:

    def __init__(self, cfg):
        self.out_list = cfg["indicator_list"]
        self.bollinger_period = cfg["indicators"]["period"]
        self.chop_period = cfg["indicators"]["chop_period"]
        self.rsi_period = cfg["indicators"]["rsi_period"]
        self.max_roc = cfg["indicators"]["max_roc"]
        self.max_volume_roc = cfg["indicators"]["max_volume_roc"]
        self.fast_period = cfg["indicators"]["fast_period"]
        self.slow_period = cfg["indicators"]["slow_period"]
        self.signal_period = cfg["indicators"]["signal_period"]
        self.roc_list = range(1, self.max_roc + 1)
        self.volume_roc_list = range(1, self.max_volume_roc + 1)
        coin = cfg["financial"]["trading_coin"]
        self.col_names = {
            'open': f'{coin}.o',
            'close': f'{coin}.p',
            'high': f'{coin}.h',
            'low': f'{coin}.l',
            'volume': f'{coin}.v'
        }

    @staticmethod
    def _standardize(row):
        return (row[0] - row[1]) / (row[2] - row[1])

    def _compute_tp(self, df):

        cols_ = [self.col_names["close"], self.col_names["high"], self.col_names["low"]]
        df["tp"] = df[cols_].apply(lambda x: (x[0] + x[1] + x[2]) / 3, axis=1)

        return df

    def _compute_rocs(self, df):
        for i, per in enumerate(self.roc_list):
            df[f"roc-{i}"] = df["tp"].pct_change(per)

        return df

    def _compute_volume_rocs(self, df):
        for i, per in enumerate(self.volume_roc_list):
            df[f"vroc-{i}"] = df[self.col_names["volume"]].pct_change(per)

        return df

    def _compute_bollinger(self, df):

        df["std"] = df["tp"].rolling(self.bollinger_period).std()
        df["min"] = df["tp"].rolling(self.bollinger_period).min()
        df["max"] = df["tp"].rolling(self.bollinger_period).max()

        df["ewm-tp"] = (
            df["tp"]
            .ewm(
                span=self.bollinger_period, min_periods=0, adjust=False, ignore_na=False
            )
            .mean()
        )
        df["lower"] = df[["ewm-tp", "std"]].apply(lambda x: x[0] - 2 * x[1], axis=1)
        df["upper"] = df[["ewm-tp", "std"]].apply(lambda x: x[0] + 2 * x[1], axis=1)

        df["bandwidth"] = df[["ewm-tp", "lower", "upper"]].apply(
            lambda x: (x[2] - x[1]) / x[0], axis=1
        )
        df["percent-b"] = df[["tp", "lower", "upper"]].apply(
            lambda x: self._standardize(x), axis=1
        )

        return df

    @staticmethod
    def _compute_cv(df):

        df["cv"] = df[["ewm-tp", "std"]].apply(lambda x: x[1] / x[0], axis=1)
        return df

    def _compute_atr(self, df):
        df["close-p"] = df[self.col_names["close"]].shift(1)

        def tr_(x):
            return max([(x[1] - x[2]), abs(x[1] - x[0]), abs(x[2] - x[0])])

        df["tr"] = df[["close-p", self.col_names["high"], self.col_names["low"]]].apply(
            tr_, axis=1
        )
        df["atr"] = (
            df["tr"].ewm(span=1, min_periods=0, adjust=False, ignore_na=False).mean()
        )
        df["atr-sum"] = df["atr"].rolling(self.chop_period).sum()

        df["max-high"] = df[self.col_names["high"]].rolling(self.chop_period).max()
        df["min-low"] = df[self.col_names["low"]].rolling(self.chop_period).min()

        return df

    def _compute_chop(self, df):
        def chop_(x):
            return np.log10(x[0] / (x[1] - x[2])) / np.log10(self.chop_period)

        df["chop"] = df[["atr-sum", "max-high", "min-low"]].apply(chop_, axis=1)

        return df

    def _compute_x(self, df):
        def x_(x):
            return (2 * x[0] - x[1]) / x[0]

        df["x"] = df[[self.col_names["close"], self.col_names["open"]]].apply(
            x_, axis=1
        )

        return df

    def _compute_rsi(self, df):
        df["diff-c"] = df[[self.col_names["close"]]].diff()

        df["up"] = df[["diff-c"]].apply(lambda x: x[0] if x[0] > 0 else 0, axis=1)
        df["down"] = df[["diff-c"]].apply(lambda x: -x[0] if x[0] < 0 else 0, axis=1)
        df["roll-up"] = (
            df["up"]
            .ewm(span=self.rsi_period, min_periods=0, adjust=False, ignore_na=False)
            .mean()
        )
        df["roll-down"] = (
            df["down"]
            .ewm(span=self.rsi_period, min_periods=0, adjust=False, ignore_na=False)
            .mean()
        )

        def rsi_(x):
            return 1.0 - 1.0 / (1.0 + x[0] / (x[1] + 1e-10))

        df["rsi"] = df[["roll-up", "roll-down"]].apply(rsi_, axis=1)

        return df

    def _get_indicator_names(self):

        # Retrieve only the indicators we are going to use in the models
        out = self.out_list.copy()
        if "macd" in out:
            out.append("macsignal")
            out.append("macdhist")

        for i, j in enumerate(self.roc_list):
            out.append("roc-" + str(i))

        for i, j in enumerate(self.volume_roc_list):
            out.append("vroc-" + str(i))

        return out

    def _compute_macd(self, df):
        df["macd"], df["macsignal"], df["macdhist"] = MACD(
            df[self.col_names["close"]],
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
            signalperiod=self.signal_period,
        )
        return df

    def _compute_chaikin_osc(self, df):
        df["chaik_osc"] = ADOSC(
            df[self.col_names["high"]],
            df[self.col_names["low"]],
            df[self.col_names["close"]],
            df[self.col_names["volume"]],
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
        )

        return df

    def get_max_indicator(self):
        return max(
            self.max_roc,
            self.max_volume_roc,
            self.bollinger_period,
            self.chop_period,
            self.rsi_period,
            # TODO: this is for MACD; needs reviewing
            self.slow_period + self.signal_period,
        )

    def get_indicator_number(self):
        num = 0
        for ind in self.out_list:
            if ind == "macd":
                num += 3
            else:
                num += 1

        return num + self.max_roc + self.max_volume_roc

    def _cut_preliminaries(self, df):
        # Cut the data at the beginning, where the indicators are not computed correctly
        return df.iloc[self.get_max_indicator():, :]

    def compute_indicators(self, df):
        # This computes all the indicators we need
        # Careful because the different parts might be using one another, so they need
        # to be computed in the same order they are written in this script

        # Typical price (TP)
        df = self._compute_tp(df)

        # Rates of change (ROCs)
        df = self._compute_rocs(df)

        # Volume rates of change
        df = self._compute_volume_rocs(df)

        bollinger_indices = ["bandwidth", "percent-b"]
        if any([a in self.out_list for a in bollinger_indices]):
            # Bollinger bands related indices (bandwidth and percent-b)
            df = self._compute_bollinger(df)

        if "cv" in bollinger_indices:
            # Coefficient of variation (CV)
            df = self._compute_cv(df)

        atr_indices = ["chop", "atr"]
        if any([a in self.out_list for a in atr_indices]):
            # Average true range (ATR): lookout, we are only using it to compute
            # other indicators
            df = self._compute_atr(df)
            # Chopiness
            df = self._compute_chop(df)

        if "x" in self.out_list:
            # X
            df = self._compute_x(df)

        if "rsi" in self.out_list:
            # Relative strength index (RSI)
            df = self._compute_rsi(df)

        if "macd" in self.out_list:
            df = self._compute_macd(df)

        if "chaik_osc" in self.out_list:
            df = self._compute_chaikin_osc(df)

        # Cut data from the beginning
        df = self._cut_preliminaries(df)

        return df[self._get_indicator_names()]
