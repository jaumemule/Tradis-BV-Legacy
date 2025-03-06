### Place a file with the name data_{COIN} and execute. Check supported coins!

import pymongo
import csv
import os
import datetime
import sys

#########################################################################################
######### MODIFY


supported_coins = ['BTC', 'ETH', 'LTC', 'USDT', 'EUR', 'ADA']
base_coin = 'USDT'


######### END MODIFY
##########################################################################################
client = pymongo.MongoClient(os.getenv('MONGO_CONNECTION'))
dbAggregated = client.aggregated
collection = dbAggregated[base_coin]

collection.create_index('date')

def update_progress(progress):
    barLength = 50 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1}% {2}".format( "="*block + " "*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()

for coin in supported_coins:

    filename = 'data_' + str(coin) + '.csv'

    if os.path.exists(filename):

        with open(filename) as f:
            total_rows = sum(1 for line in f)

        with open(filename, 'r') as file:
            my_reader = csv.reader(file, delimiter=',')

            print('inserting for ', coin, ' in base coin ', base_coin, ' a total of ', total_rows)

            progress_row = 0
            for row in my_reader:

                if progress_row == 0:
                    progress_row += 1
                    continue

                if progress_row % 1000 == 0:
                    progress_bar = (progress_row / total_rows)
                    update_progress(progress_bar)

                date = row[0]
                date = date.split('+')[0]
                date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

                result = collection.find_one({"date" : date})

                if result == None:
                    result = {}

                result['date'] = date
                result[coin] = {}
                result[coin]['o'] = row[1]
                result[coin]['h'] = row[2]
                result[coin]['l'] = row[3]
                result[coin]['p'] = row[4]
                result[coin]['v'] = row[5]
                key = {'date': date}

                collection.update_one(key, {"$set": result}, upsert=True)

                progress_row+=1

            print('Total inserted rows: ', progress_row, ' for ', coin)
