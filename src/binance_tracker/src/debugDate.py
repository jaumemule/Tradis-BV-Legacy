# helper functions
import pymongo
from pandas.io.json import json_normalize
import datetime

dbclient = pymongo.MongoClient('mongodb://mongo:27017/')
database = dbclient.aggregated
binance_aggregation = database['binance_aggregation']

now = datetime.datetime(2017, 9, 1, 0, 0, 0)

findDate = now
untilBackup = now + datetime.timedelta(minutes=- int(10))

print('-------LOADING DATA FOR PREDICTIONS AT', str(findDate), 'until', str(untilBackup))

data = list(binance_aggregation.find({"date": {'$gte': untilBackup, '$lt': findDate}}))

if len(data) == 0:
    raise Exception('No data: ' + str(findDate))
else:
    df = json_normalize(data).transpose()

df.columns = df.loc["date"]

# print(list(df.columns.values))

print(df)
