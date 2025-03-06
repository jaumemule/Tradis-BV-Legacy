import pandas as pd
import numpy as np
from os.path import join
import pymongo
from pandas.io.json import json_normalize
import datetime

from sklearn.preprocessing import RobustScaler, LabelEncoder


class Data(object):

    def __init__(self, cfg):
        self.seq_len = cfg["training"]["seq_len"]
        self.forecast_len = cfg["training"]["forecast_len"]
        self.interval = cfg["training"]["interval"]
        self.percentages = cfg["financial"]["percentages"]
        self.amount = cfg["financial"]["amount"]
        self.fee = cfg["financial"]["fee"]
        self.scale = cfg["training"]["scale"]
        self.coin_list = cfg['training']['coin_list']
        self.toy = False

    def import_from_csv(self, data_path, filename):

        filename = join(data_path, filename)
        df = pd.read_csv(filename,
                        error_bad_lines=False,
                        index_col=0,
                        encoding='latin-1',
                        engine='python')

        self.df = df

    def import_from_db(self, first_date, day_number):
        end_date = first_date + datetime.timedelta(days=day_number)
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client.aggregated
        collection = db.binance_aggregation

        data = list(collection.find({"date": {'$gte': first_date, '$lt': end_date}}))
        df = json_normalize(data)
        df = df.sort_values('date', ascending=True)
        df.index = df["date"]
        df = df.drop(["_id", "date"], axis=1)
        df = df.transpose()

        # convert to numeric
        df[df.columns] = df[df.columns].apply(pd.to_numeric, errors='coerce')
        self.df = df

    def check_data(self):
        if self.df.isnull().sum().sum() > 0:
            raise ValueError("There are missings in the data. Exiting.")

    def filter_coins(self):
        df = self.df
        with open(self.coin_list) as f:
            filtered_coins = f.readlines()
        filtered_coins = [x.strip() for x in filtered_coins]
        temp_coins = [a for a in list(df.index) if a.split('.')[0] in filtered_coins]
        df_filtered = df[df.index.isin(temp_coins)]

        self.df = df_filtered
        return filtered_coins  # return the list of coins to be used later on

    def create_raw(self):
        df = self.df
        which_prices = [a for a in list(df.index) if a.split('.')[1] == 'p']
        df_raw = df[df.index.isin(which_prices)]
        df_raw.index = [a.split('.')[0] for a in list(df_raw.index)]
        self.df_raw = df_raw

    def raw_test(self, i):
        df_raw = self.df_raw
        seq_len = self.seq_len
        forecast_len = self.forecast_len

        x = df_raw.iloc[:, i * forecast_len + seq_len]
        y = df_raw.iloc[:, (i + 1) * forecast_len + seq_len]

        return x, y

    def train(self, model_type="linear"):
        df = self.df
        df_raw = self.df_raw
        seq_len = self.seq_len
        forecast_len = self.forecast_len
        interval = self.interval
        scale = self.scale

        fd = df.transpose()  # need to transpose because StandardScaler only works on rows
        fd = fd.pct_change().replace([np.inf, -np.inf], np.nan).ffill()
        fd = fd.iloc[1:].fillna(0)
        if scale:
            fd = RobustScaler().fit_transform(fd)
            df = fd.transpose()

        else:
            df = fd.transpose().values

        # Initialization of training arrays:
        X_train = np.zeros((int((df.shape[1] - seq_len - forecast_len)/interval), df.shape[0], seq_len))
        y_train = np.zeros((int((df.shape[1] - seq_len - forecast_len)/interval), df_raw.shape[0]))

        # Populating the arrays with the original data from df.
        for index in range(X_train.shape[0]):
            X_train[index, :, :] = df[:, index * interval: index * interval + seq_len]

        X_train = np.swapaxes(X_train, 1, 2)  # set coins in the third dimension

        for index in range((int((seq_len + forecast_len)/interval)), int((df.shape[1]-forecast_len)/interval)):
            y_train[index - int((seq_len + forecast_len)/interval), :] = df_raw.iloc[:, index*interval]/df_raw.iloc[:, index*interval-forecast_len] - 1

        if model_type == "sigmoid":
            # If it's a classification model create the one hot test instances
            y_train = np.where(y_train >= 0, 1, 0)
            if np.isnan(y_train).sum() > 0:  # Probably not needed here, but just in case
                raise ValueError("There are nans. Exiting.")
            y_train = np.array([LabelEncoder().fit_transform(y) for y in y_train])

        return X_train, y_train

    def test(self, model_type="linear"):
        seq_len = self.seq_len
        forecast_len = self.forecast_len
        df = self.df
        scale = self.scale

        which_prices = [a for a in list(df.index) if a.split('.')[1] == 'p']
        df_raw = df[df.index.isin(which_prices)].values

        fd = df.transpose()
        fd = fd.pct_change().replace([np.inf, -np.inf], np.nan).ffill()
        fd = fd.iloc[1:]  # FIXME: treat this differently
        fd = fd.fillna(0)
        date_values = fd.index

        if scale:
            fd = RobustScaler().fit_transform(fd)
            df = fd.transpose()
        else:
            df = fd.transpose().values

        X_test = np.zeros((int((df.shape[1] - seq_len - forecast_len) / forecast_len), df.shape[0], seq_len))
        y_test = np.zeros((int((df.shape[1] - seq_len - forecast_len) / forecast_len), df_raw.shape[0]))
        y_test_dates = list()

        for index in range(X_test.shape[0]):
            X_test[index, :, :] = df[:, index * forecast_len: index * forecast_len + seq_len]
            y_test[index, :] = df_raw[:, index * forecast_len + seq_len + forecast_len]/df_raw[:, index * forecast_len + seq_len] - 1
            y_test_dates.append(date_values[index * forecast_len + seq_len + forecast_len])

        X_test = np.swapaxes(X_test, 1, 2)

        if model_type == "sigmoid":
            y_test = np.where(y_test >= 0, 1, 0)
            y_test = np.array([LabelEncoder().fit_transform(y) for y in y_test])

        return X_test, y_test, y_test_dates

    def predict_function(self, X_test, model):

        preds = model.predict(X_test)
        predictions = pd.DataFrame(preds.transpose(), index=self.df.index, columns=["value"])

        if predictions['value'].isnull().sum() > 0:
            raise ValueError("There are NaNs in the predictions. Exiting.")

        investments = predictions.sort_values(by="value", ascending=False)[:5]

        return list(investments.index)

    def predict_coins(self, X_test, model):
        return [self.predict_function(x, model) for x in X_test]

    @staticmethod
    def predict_and_compare_function(X_test, y_test, model):
        preds = model.predict(X_test)
        return (np.subtract(preds, y_test)**2).sum()

    def predict_and_compare(self, X_test, y_test, model):
        return [self.predict_and_compare_function(x, y, model) for (x, y) in zip(X_test, y_test)]

    def investment(self, coins_historical):
        # another helper function to compute simulated rewards for investments
        percentages = self.percentages
        amount = self.amount
        fee = self.fee
        check = False

        amount_historical = []
        for i in range(coins_historical.shape[0]):
            x, y = self.raw_test(i)

            if check and coins_historical.iloc[i-1].equals(coins_historical.iloc[i]):
                temp_fee = 0
            else:
                temp_fee = fee
            check = True

            coins = coins_historical.iloc[i, :]
            difs = (y.loc[coins] - x.loc[coins]) / x.loc[coins]
            amounts = [amount * p for p in percentages]
            amounts = amounts * np.repeat(1 - temp_fee, len(percentages)) * (1 + difs)
            amount = sum(amounts)
            amount_historical.append(amount)

        return amount_historical, round(amount, 2)
