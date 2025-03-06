import pymongo
import os
import pandas as pd
import datetime

### MAKE A COPY OF STAGING FROM THE DESIRED COLLECTIONS ####
### WILL REMOVE ALL THE OTHER COLLECTIONS THAT ARE NOT LISTED IN THE EXCEPTIONS ####


remoteClient = pymongo.MongoClient('mongodb://tradis-production:xxxxxxxxx/aggregated?replicaSet=rs-ds129605&retryWrites=false')
remoteDb = remoteClient.aggregated

collection = 'transactions_procyon_USDT_real_money'
remoteCollection = remoteDb[collection]

data = pd.read_csv('corrected_data_procyon.csv')
data = data.to_dict('list')

aggregation = []
for key, item in enumerate(data['at']):

    date = data['at'][key]
    date = date.split('.')[0]

    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    aggregation.append({
        'at' : date,
        'totalBtcBeforeTrading' : data['totalBtcBeforeTrading'][key],
        'USDvalue' : data['USDvalue'][key],
        'BNBvalue' : 0,
        'BTCvalue' : data['BTCvalue'][key],
        'totalUSDBeforeTrading' : data['USD'][key],
        'transactionMessages': [],
        'AIpredictions': [],
        'repeatedPredictionsRegardingPreviousOne': [],
        'traderIntendedToBuy': [],
        'traderIntendedToSell': [],
        'previousInvestmentWithCurrentCoinValue': {},
        'predictedCoinsWithCurrentCoinValue': {},
        'previousCoinsWithMoney': [],
    })

for doc in aggregation:
    remoteCollection.insert_one(doc)
