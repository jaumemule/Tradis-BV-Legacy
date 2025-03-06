import datetime
import pymongo
import csv
import pandas as pd

mongoConnection = 'mongodb://localhost:27017/'
dbclient = pymongo.MongoClient(mongoConnection)
database = dbclient.aggregated
collection = database['USDT']

initialDate = datetime.datetime(2020, 9, 1, 0, 0, 0)

days = 200
position = 0

output = []

def minutes_difference(d1, d2):
    return (d2 - d1).total_seconds() / 60.0


while days > 0:


    findDate = initialDate + datetime.timedelta(hours=-24)
    untilBackup = findDate + datetime.timedelta(hours=- 24)  # start 24 hours before

    print('---- next day', str(untilBackup))

    data = list(collection.find({"date": {'$gte': untilBackup, '$lt': findDate}}, {'date': 1}))

    if len(data) == 0:
        print('no data')

    dates = []
    for key, item in enumerate(data):

        dates.append(item['date'])

        # find missings
        nextKey = key+1

        try:
            next_db_date = data[nextKey]['date']
            currentDate = data[key]['date']
            minutes_difference_to_next_one = minutes_difference(currentDate, next_db_date)

            if minutes_difference_to_next_one != 1:
                dateMissing = currentDate
                for minute_missing in range(int(minutes_difference_to_next_one)):
                    dateMissing = dateMissing + datetime.timedelta(minutes=+1)
                    output.append([position, dateMissing, 'no'])

                    print('missing', dateMissing)
        except IndexError:
            # Key is not present
            continue

        isExistant = 'no'

        if 'date' not in item:
            date = item['date']
            print('BTC missing at', item['date'])
            isExistant = 'no'
            output.append([position, date, isExistant])

        # else:
        #     date = item['date']
        #     # print(item['USDT']['p'], item['date'])
        #     isExistant = 'yes'

        position += 1

    df = pd.DataFrame(dates)
    duplicates = df[df.duplicated(keep=False)]
    duplicates = list(duplicates)

    if len(duplicates) == 1:
        print('             + no duplicates')
    else:
        print('----- duplicates found -----', duplicates)

    dates = []

    del data
    initialDate = findDate

    days -= 1

    with open('missings.csv', 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(output)

    csvFile.close()