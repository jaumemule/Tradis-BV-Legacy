# This script analyzes the data that will be fed into the director and completes it or
# fixes it if needed

import numpy as np
import pandas as pd


class DataAnalyzer:

    # After how many missing minutes should we abort
    abort_len = 10000
    # When missing data becomes worrisome
    super_warn_len = 10
    # When we start removing duplicated data
    duplicated_len = 10

    def __init__(self, start_date, end_date, slack_client, verbose=True):
        self.start_date = start_date
        self.end_date = end_date
        self.slackClient = slack_client
        self.verbose = verbose

    @staticmethod
    def _clean_db_output(df):
        df = df.sort_values("date", ascending=True)
        df.index = df["date"]

        return df.drop(["_id", "date"], axis=1)

    def _check_shape(self, df):
        if df.shape[1] < 2:
            message = f"No data found in data provider at: {self.start_date}. Aborting."
            self.slackClient.send(message)

            raise RuntimeError("No data.")

    @staticmethod
    def _to_float(df):
        return df.astype(np.float64)

    def _should_abort(self, mis_index):
        _timestamp = mis_index[0].strftime("%d-%m-%Y, %H:%M:%S")
        if len(mis_index) >= self.abort_len:
            if self.verbose:
                message = (
                    f"There were too many missings ({len(mis_index)}) after "
                    f"timestamp {_timestamp}. Aborting."
                )
                self.slackClient.send(message)

            raise RuntimeError("Not enough data.")

    def _complete_data(self, df):

        # Create df with full index
        objective_index = pd.date_range(
            start=self.start_date, end=self.end_date, freq="min", closed="right"
        )
        simulated_df = pd.DataFrame(index=objective_index)

        complete_df = pd.merge(
            df, simulated_df, left_index=True, right_index=True, how="right"
        )

        # Find missings
        _mis = complete_df.isnull().sum(axis=1) > 0
        mis_index = complete_df[_mis].index
        if any(_mis):
            self._should_abort(mis_index)
            if self.verbose:
                if len(mis_index) < self.super_warn_len:
                    message = (
                        f"Warning: we are missing data for "
                        f"{[a.strftime('%d-%m-%Y, %H:%M:%S') for a in mis_index]}."
                        f"I am inputting them."
                    )
                else:
                    message = (
                        f"Super warning: we are missing {len(mis_index)} minutes, "
                        f"I am imputing them but you should rethink what you are doing "
                        f"with your life."
                    )
                self.slackClient.send(message)

            complete_df = complete_df.interpolate(method="linear").bfill().ffill()

        return complete_df

    def _check_constant(self, df):
        # In some occasions binance might feed us repeated data and this will throw off
        # the computations, probably even adding infinities. We check for this here

        temp = df.copy()
        # Shift by as many ranges we need to easily compute equalities
        for i in range(1, self.duplicated_len + 1):
            temp[f"shift_{i}"] = temp.iloc[:, 0].shift(-i)

        # Are there any constant of size self.duplicated_len or longer ranges?
        constant_periods = temp.index[
            temp.std(axis=1, skipna=False) == 0
        ]
        # If so, fix it
        if any(constant_periods):
            message = (
                f"There were more than {self.duplicated_len} repeated values in "
                f"{df.columns}. Removing them."
            )
            self.slackClient.send(message)

            # The previous algorithm only flags the first entry of any range, here we
            # refill the rest of the constant values
            problematic_indices = [
                pd.date_range(start=a, periods=self.duplicated_len + 1, freq="min")[1:]
                for a in constant_periods
            ]
            flat_list = [item for sublist in problematic_indices for item in sublist]
            # There are duplicates, which we remove
            clean_indices = [a for a in set(flat_list) if a in df.index]

            # Set to missing
            df.loc[clean_indices, df.columns[0]] = np.nan

            return df, True

        else:
            return df, False

    def analyze(self, df, verbose):
        self._check_shape(df)
        df = self._clean_db_output(df)
        df = self._to_float(df)

        # Check for missing data
        target_shape = (self.end_date - self.start_date).total_seconds() / 60
        if df.shape[0] < target_shape:
            df = self._complete_data(df)
            verbose = False  # only warn once

        # Check for constant data
        df, constant_data = self._check_constant(df)
        if constant_data:
            df = self._complete_data(df)
            verbose = False

        return df, verbose

    def analyze_non_reals(self, df):
        inf_num = df.gt(1e10).sum().sum() + df.lt(-1e10).sum().sum()
        mis_num = df.isnull().sum().sum()

        if inf_num + mis_num > self.abort_len:
            message = (
                f"ALERT: there were {inf_num} infinities and/or {mis_num} in "
                f"the data. This is above the threshold, so I am aborting."
            )
            self.slackClient.send(message)
            raise RuntimeError("Too many infinities or missing data.")
        elif inf_num + mis_num:
            message = f"There were {inf_num} infinities and/or {mis_num} missings. " \
                      f"I am imputing them."
            self.slackClient.send(message)
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.interpolate(method="linear").bfill().ffill()

        return df
