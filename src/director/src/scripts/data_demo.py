import datetime
import pymongo

client = pymongo.MongoClient('mongodb://mongo:27017/')
dbAggregated = client.aggregated
collection = dbAggregated['USDT']

now = datetime.datetime(2018, 1, 4, 23, 0, 0)
findDate = now
untilBackup = now + datetime.timedelta(minutes=- 2000)  # start 180 hours before

print(findDate, untilBackup)
data = list(collection.find({"date": {'$gte': untilBackup, '$lt': findDate}}))

dates = []
for key, item in enumerate(data):
    dates.append(str(item['date']))

print(dates)