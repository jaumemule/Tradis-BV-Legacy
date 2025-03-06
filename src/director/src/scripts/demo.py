import datetime
import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
dbAggregated = client.aggregated
collection = dbAggregated['USDT']

now = datetime.datetime(2019, 10, 29, 0, 0, 0)
findDate = now
untilBackup = now + datetime.timedelta(minutes=- 30)  # start 180 hours before

print(findDate, untilBackup)
data = list(collection.find({"date": {'$gte': untilBackup, '$lt': findDate}}, {'BTC.v' :1, 'BTC.p' :1, 'date': 1}))

print(data)

for item in data:

    if 'BTC' not in item:
        print('BTC missing at', item['date'])
    else:
        print(item['BTC']['p'], item['date'])
