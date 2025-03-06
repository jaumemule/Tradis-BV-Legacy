import requests
import datetime
import numpy as np
import pandas as pd
import time
import math
import schedule
from slackclient import SlackClient
from random import randint
import sys
import pymongo
from time import sleep
import pprint
import os

if(os.getenv('ENVIRONMENT') == 'production'):
    mongoDbUrl = os.getenv('MONGO_CONNECTION')
else:
    mongoDbUrl = 'mongodb://mongo:27017/'

client = pymongo.MongoClient()
client = pymongo.MongoClient(mongoDbUrl)
db = client.crypto
dbAggregated = client.aggregated

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

machine_number = randint(0, 999)

def InstantExchanges(compare_coin, df, machine_number):
    index = list(df.index)
    maximum = 60
    steps = round(len(index)/maximum)

    # the maximum and steps shenanigans are because the server only allows for
    # 60 simultanious coin exchanges
    timing = datetime.datetime.utcnow()
    aggregateList = {"date": timing};

    for i in range(steps+1):

        scoin = ",".join(list(index)[maximum*i:maximum*(i+1)])
        url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms={}'\
            .format(scoin, compare_coin)

        try:
            page = requests.get(url)
            data = page.json()

            for element in data['RAW']:           
                aggregateList[element] = {"p" : 0, "v" : 0};
                aggregateList[element]['p'] = data['RAW'][element][compare_coin]['PRICE']
                aggregateList[element]['v'] = data['RAW'][element][compare_coin]['VOLUME24HOUR']

        except:
            print("ERROR ON API CRYPTOCOMPARE")
            SendNotification("failure")
            sys.exit(0)
                      
    if (os.environ['ENVIRONMENT'] == 'dev'):
        print("retry....")

    postAggregation = dbAggregated['BTC']
    postAggregation.insert_one(aggregateList).inserted_id
   
    return df

def AcquireAllExchanges(df):
    # Reads the csv with the previous information
    df = pd.read_csv("CoinNames.csv",index_col=0)
    try:
        df_prov = InstantExchanges('BTC', df, machine_number) # we can change the reference coin here
    except:
        SendNotification("ExternalServerDown")
        sys.exit(0)

slack_token = "xxx"
sc = SlackClient(slack_token)

def SendNotification(which):
    if (os.getenv('ENVIRONMENT') == 'production'):
        if (which == "failure"):
            sc.api_call(
                "chat.postMessage",
                channel="#notifications",
                text="Data retrieval is down on machine " + str(machine_number) + " :cold_sweat: :cold_sweat:"
                )
        if (which == "isUp"):
            sc.api_call(
                "chat.postMessage",
                channel="#notifications",
                text="Tracking just started on machine " + str(machine_number) + " :sunglasses:"
                )
        if (which == "ExternalServerDown"):
            sc.api_call(
                "chat.postMessage",
                channel="#notifications",
                text="Cryptocompare server is down! :shit:"
                )
        if (which == "NoPrint"):
            sc.api_call(
                "chat.postMessage",
                channel="#notifications",
                text="Can't write to csv :no_good:"
                )
# disabled functionality. too annoying :P
def SendNotificationStillUp():
    sc.api_call(
        "chat.postMessage",
        channel="#notifications",
        text="Tracking on machine " + str(machine_number) + " is still working :grin:"
        )

# the following is the inner cron that triggers the functions every minute
print("STARTING PYTHON SCRIPT JOB SET PER MINUTE")

# Import the coin names and create the dataframe
cd = pd.read_csv('CoinNames.csv', error_bad_lines=False)
# Here we have a pandas dataframe with only the index with 866 coin names.
once_per_minute = CronTrigger('*', '*', '*', '*', '*', '*', '*', '0')
once_per_hour = CronTrigger('*', '*', '*', '*', '*', '*', '0', '0')
scheduler = BackgroundScheduler()

scheduler.start()

SendNotification("isUp")

scheduler.add_job(AcquireAllExchanges, trigger=once_per_minute, args = [cd], max_instances=100)

# disabled functionality. too annoying :P
# if(os.getenv('ENVIROMENT') == 'production'):
#     scheduler.add_job(SendNotificationStillUp, trigger=once_per_hour, max_instances=100)

print("Machine ON: " + str(machine_number))
sleep(100000000) # the script will last around 4 years
