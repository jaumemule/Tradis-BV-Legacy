import pymongo
from pandas.io.json import json_normalize
import pandas as pd
import datetime
import os
from os.path import join


path = os.getcwd()
data_path = os.path.join(path, "data")
data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
how_many = len(data_files)


def data_loop():
    first_date = pd.to_datetime("2018-03-20 12:36:00", infer_datetime_format=True)
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client.aggregated
    collection = db.BTC_historical

    more = True
    date = first_date + datetime.timedelta(days=30 * (max(how_many, 1) - 1))
    i = how_many
    while more:
        end_date = date + datetime.timedelta(days=30)
        data = list(collection.find({"date": {'$gte': date, '$lt': end_date}}))
        df = json_normalize(data)
        df.index = df["date"]
        df = df.drop(["_id", "date"], axis=1).transpose()
        df.to_csv("data_" + str(i) + ".csv")

        if df.shape[1] < 40000:
            more = False

        date = end_date
        i += 1


def data_reduce(data_files):
    dates = pd.DataFrame()
    i = 1
    for file in data_files:
        filename = join(data_path, file)
        df = pd.read_csv(filename,
                         error_bad_lines=False,
                         index_col=0,
                         encoding='latin-1',
                         engine='python')

        # nan cleaning: we eliminate coins with more than 30 missing values.
        df = df[df.isnull().sum(axis=1) < 30]

        # convert to numeric
        for col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # interpolate the rest of the missing data
        df = df.interpolate(axis=1, limit=30)
        filtered_coins = pd.read_csv("binance_markets_in_bnb_bo.csv", index_col = 0)
        filtered_coins = list(filtered_coins.index)
        df = df[df.index.isin(filtered_coins)]
        df.to_csv(join("data", "reduced_data_" + str(i) + ".csv"))
        dates[i] = [df.columns[1], df.columns[-1]]
        i += 1

    dates.to_csv('dates.csv')


# data_reduce(data_files)

def join_data():
    path = os.getcwd()
    data_path = os.path.join(path, "reduced_data")
    data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
    df_tot = pd.read_csv(join("reduced_data", data_files[0]),
                     error_bad_lines=False,
                     index_col=0,
                     encoding='latin-1',
                     engine='python')

    for file in data_files[1:]:
        df = pd.read_csv(join("reduced_data", file),
                         error_bad_lines=False,
                         index_col=0,
                         encoding='latin-1',
                         engine='python')

        df_tot = df_tot.join(df)
        print(df_tot.shape)

    df_tot.to_csv("reduced_data.csv")


# join_data()


def data_check():

    filtered_coins = pd.read_csv("binance_markets_in_bnb.csv", index_col=0)
    filtered_coins = list(filtered_coins.index)
    for file in data_files:
        filename = join(data_path, file)
        df = pd.read_csv(filename,
                         error_bad_lines=False,
                         index_col=0,
                         encoding='latin-1',
                         engine='python')

        # nan cleaning: we eliminate coins with more than 30 missing values.
        df = df[df.isnull().sum(axis=1) < 30]

        # convert to numeric
        for col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # interpolate the rest of the missing data
        df = df.interpolate(axis=1, limit=30)
        dif = [a for a in filtered_coins if a not in list(df.index)]

        print("The difference in set " + str(file) + " is ", str(dif))


data_check()


def data_filter():
    path = os.getcwd()
    
    data_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    with open('20_coins.csv') as f:
        filtered_coins = f.readlines()
        filtered_coins = [x.strip() for x in filtered_coins]

    i=1
    for file in data_files:
        df = pd.read_csv(file,
                         error_bad_lines=False,
                         index_col=0,
                         encoding='latin-1',
                         engine='python')

        
        df_filtered = df[df.index.isin(filtered_coins)]
        df_filtered.to_csv('reduced_data_' + str(i) + '.csv')
        i+=1