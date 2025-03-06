# uses the date_to_milliseconds and interval_to_milliseconds functions
# https://gist.github.com/sammchardy/3547cfab1faf78e385b3fcb83ad86395
# https://gist.github.com/sammchardy/fcbb2b836d1f694f39bddd569d1c16fe
# https://gist.github.com/sammchardy/0c740c40276e8f05b6390ce304476605
# https://api.binance.com/api/v1/klines?symbol=TUSDBTC&interval=1m

### NOTES ####
# TUSD disappears from BTC markets on 2019-04-01, then we take BTC from TUSD market and revert it!

# FOR TUSD, DO:
# python import.py --from 2019-08-16 --days 2 --market TUSD --coins BTC --revert-market

# python import.py --from 2019-09-15 --days 180 --market TUSD --coins BTC --revert-market

# python import.py --from 2018-06-17 --days 300 --coins TUSD --market BTC

# python import.py --from 2017-12-01 --days 200 --coins TUSD --market BTC

from binance.client import Client
import dateparser
import pytz
from datetime import datetime, timedelta
import pymongo
import time
import gc
from slackclient import SlackClient
import sys, getopt
import os
import numpy as np
import pandas as pd

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:f:h:c:m:r', ['days=', 'from=', 'until=', 'days=', 'help', 'coins=', 'market=', 'revert-market'])
except getopt.GetoptError:
    sys.exit(2)

days = None
start_at = None
until_date = None
days_to_substract = None
coinsFromInput = None
marketFromInput = None
revertMarket = False
for opt, arg in opts:
    if opt in ('-h', '--help'):
        print('RUN format: python import.py --from 2019-03-19 --until 2019-03-20, will track to the past. both are mandatory arugments. also, --coins is an optional argument. pass them as a list: "BTC, ETH" and --market is also optional. if you pass only one coin, is possible to revert the price by passing the flag --revert-market: BTC/TUSD will now be TUSD/BTC')
        sys.exit(2)
    elif opt in ('-f', '--from'):
        start_at = arg
    elif opt in ('-u', '--until'):
        until_date = arg
    elif opt in ('-d', '--days'):
        days = arg
    elif opt in ('-c', '--coins'):
        coinsFromInput = arg
    elif opt in ('-m', '--market'):
        marketFromInput = arg
    elif opt in ('-r', '--revert-market'):
        revertMarket = True
    else:
        print('incorrect argument list')
        sys.exit(2)

converted_until_date = datetime.strptime(str(until_date) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')

if days and not start_at:
    start_at = converted_until_date - timedelta(days=int(days))
else:
    start_at = datetime.strptime(str(start_at) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')

delta = converted_until_date - start_at
days_to_substract = delta.days + 1

if not days_to_substract or not until_date and (not start_at or not days):
    raise Exception('Incorrect argument list, run python import.py --help')

### CONFIGURE ###

print('-----',coinsFromInput, marketFromInput)

interval = '1m'        # one minute
baseCoin = 'USDT'      # market
targetCoin = ['ENJ','XRP','ETH','BAT','BNB','MANA','EOS','ICX','BCHSV','TUSD','MDA','RCN','LTC','THETA','LOOM','ONT','TRX','BCHABC','ELF','BTT','NEO','XLM','ADA','LUN','LINK','VET','RVN','HOT','XMR','RDN','ZRX','ARN','STEEM','NPXS','OMG','WAVES','OST','IOST','ZIL','MITH','WTC','APPC','DASH','GVT','QKC','ZEC','STORJ','WABI','INS','WAN','DNT','ONG','RLC','VIBE','CND','KMD','GO','NANO','AE','STRAT','IOTA','LRC','CMT','VIA','MTL','BLZ','MFT','AION','DENT','ARK','GTO','KNC','MCO','DLT','ADX','VIB','BQX','GRS','POWR','PHX','OAX','QTUM','ETC','XEM','CVC','XVG','AST','BCPT','REN','POLY','TNT','POE','SNT','YOYO','WPR','SC','HC','KEY','GNT','AMB','BTS','FUEL','EVX','BCD','DOCK','DATA','SYS','QLC','REP','NAS','LSK','BTG','SKY','ZEN','POA','STORM','FUN','AGI','SNGLS','PPT','GXS','ENG','DGD','GAS','NULS','CDT','QSP','DCR','MTH','XZC','LEND','NXS','NCASH','IOTX','TNB','PIVX','REQ','NEBL','ARDR','NAV','BRD','SNM','BNT','EDO']

if coinsFromInput:
    baseCoin = marketFromInput

if coinsFromInput:
    coinsFromInput = coinsFromInput.replace(" ", "")
    targetCoin = coinsFromInput.split(",")

# start_at = datetime.strptime(str(start_at) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
print('starting at', start_at, ' and incrementing days')

### CONFIGURE ###

mongoConnection = os.getenv('MONGO_CONNECTION')

if not mongoConnection:
    mongoConnection = 'mongodb://localhost:27017/'

dbclient = pymongo.MongoClient(mongoConnection)
database = dbclient.aggregated
binance_aggregation = database['USDT']

slackToken = os.getenv('SLACK_TOKEN')
SlackClientSdk = SlackClient(slackToken)

# create the Binance client, no need for api key
client = Client("", "")

def date_to_milliseconds(date_str):
    """Convert UTC date to milliseconds
    If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/
    :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
    :type date_str: str
    """
    # get epoch value in UTC
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d = dateparser.parse(date_str)
    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)

def interval_to_milliseconds(interval):
    """Convert a Binance interval string to milliseconds
    :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
    :type interval: str
    :return:
         None if unit not one of m, h, d or w
         None if string not in correct format
         int value of interval in milliseconds
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms

def get_historical_klines(symbol, interval, start_str, end_str=None):
    """Get Historical Klines from Binance
    See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/
    If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Biannce Kline interval
    :type interval: str
    :param start_str: Start date string in UTC format
    :type start_str: str
    :param end_str: optional - end date string in UTC format
    :type end_str: str
    :return: list of symbol values
    """

    # init our list
    output_data = []

    # setup the max limit
    limit = 500

    # convert interval to useful value in seconds
    timeframe = interval_to_milliseconds(interval)

    # convert our date strings to milliseconds
    start_ts = date_to_milliseconds(start_str)

    # if an end time was passed convert it
    end_ts = None
    if end_str:
        end_ts = date_to_milliseconds(end_str)

    idx = 0

    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set

        try:
            temp_data = client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_ts,
                endTime=end_ts
            )
        except:
            message = ':face_with_rolling_eyes: Got exception from binance tracker and *MAYBE* retried at ' + start_str + ' / ' + symbol + '. Check it out!!!'
            print(message)

            return []

        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True

        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(0.1)

    return output_data


start_time = time.time()
now = datetime.today()
counter = 0
lastStoredDate = None
isFirstItem = True
needsInterpolation = []

def serializeAndStore(item, coin):

    open = float(item[1])
    high = float(item[2])
    initialHigh = float(item[2])
    low = float(item[3])
    price = float(item[4])
    volume = float(item[5])
    taker_buy_base_asset_volume = float(item[9])
    # in case we capture a coin from a different base market

    ### HISTORY ###

    # 0 1499040000000, // Open time
    # 1 o "0.01634790", // Open
    # 2 h "0.80000000", // High
    # 3 l "0.01575800", // Low
    # 4 p "0.01577100", // Close (final price)
    # 5 v "148976.11427815", // Volume
    # 6 1499644799999, // Close time // NOT IN USE
    # 7 qv "2434.19055334", // Quote asset volume // NOT IN USE
    # 8 t 308, // Number of trades // NOT IN USE
    # 9 tbv "1756.87402397", // Taker buy base asset volume
    # 10 tqv "28.46694368", // Taker buy quote asset volume // NOT IN USE
    # 11 "17928899.62484339" // Ignore

    if revertMarket == True:
        coin = baseCoin
        open = round(1 / open, 10)
        high = round(1 / low, 10)
        low = round(1 / initialHigh, 10)
        volume = round(volume * price, 10)
        taker_buy_base_asset_volume = round(taker_buy_base_asset_volume * price, 10)
        price = round(1 / price, 10)

    result['date'] = date
    result[coin] = {}
    result[coin]['o'] = str(open)
    result[coin]['h'] = str(high)
    result[coin]['l'] = str(low)
    result[coin]['p'] = str(price)
    result[coin]['v'] = str(volume)
    result[coin]['tbv'] = str(taker_buy_base_asset_volume)
    key = {'date': date}

    storeOrUpdateResult(key, result)

    del item

def storeOrUpdateResult(key, result):
    binance_aggregation.update_one(key, {"$set": result}, upsert=True)

def insertResult(result):
    binance_aggregation.insert(result, check_keys=False)

def generateMockData(lastStoredResultDate):
    for x in range(1, 5761):  # create 2 days of dummy data
        lastStoredDate = lastStoredResultDate + timedelta(minutes=+x)
        dummyResult = {}
        dummyResult['date'] = lastStoredDate
        key = {'date': lastStoredDate}
        storeOrUpdateResult(key, dummyResult)

    print('generated missing')

### TODO indicators are hardcoded. improve this ###
### TODO indicators are hardcoded. improve this ###
### TODO indicators are hardcoded. improve this ###
def interpolate(coin):
    if len(needsInterpolation) > 0:

        for interpolation in needsInterpolation:

            data = list(binance_aggregation.find({"date": {'$gte': interpolation['init'], '$lt': interpolation['end']}}))

            firstItemWithData = data[0]

            lastFoundItem = None
            listToInterpolate = []
            listToInterpolate.append(firstItemWithData)

            for key, item in enumerate(data):

                if coin not in item and key != 0:
                    print('coin not in item' ,key)
                    item[coin] = {}
                    item[coin]['o'] = np.nan
                    item[coin]['h'] = np.nan
                    item[coin]['l'] = np.nan
                    item[coin]['p'] = np.nan
                    item[coin]['v'] = np.nan
                    item[coin]['tbv'] = np.nan

                    listToInterpolate.append(item)
                elif coin in item and key != 0:
                    print('coin in item' ,key)
                    lastFoundItem = item
                    listToInterpolate.append(lastFoundItem)
                    break

            indicator1 = []
            indicator2 = []
            indicator3 = []
            indicator4 = []
            indicator5 = []
            indicator6 = []

            for key, item1 in enumerate(listToInterpolate):
                indicator1.append(float(item1[coin]['o']))
                indicator2.append(float(item1[coin]['h']))
                indicator3.append(float(item1[coin]['l']))
                indicator4.append(float(item1[coin]['p']))
                indicator5.append(float(item1[coin]['v']))
                indicator6.append(float(item1[coin]['tbv']))
                # df = pd.DataFrame(listToInterpolate)

            s1 = pd.Series(indicator1)
            s2 = pd.Series(indicator2)
            s3 = pd.Series(indicator3)
            s4 = pd.Series(indicator4)
            s5 = pd.Series(indicator5)
            s6 = pd.Series(indicator6)

            interpolation1 = s1.interpolate()
            interpolation2 = s2.interpolate()
            interpolation3 = s3.interpolate()
            interpolation4 = s4.interpolate()
            interpolation5 = s5.interpolate()
            interpolation6 = s6.interpolate()

            list1 = interpolation1.values.tolist()
            list2 = interpolation2.values.tolist()
            list3 = interpolation3.values.tolist()
            list4 = interpolation4.values.tolist()
            list5 = interpolation5.values.tolist()
            list6 = interpolation6.values.tolist()

            for key, databaseItem in enumerate(listToInterpolate):

                if '_id' in databaseItem:
                    del databaseItem['_id']

                databaseItem[coin]['o'] = list1[key]
                databaseItem[coin]['h'] = list2[key]
                databaseItem[coin]['l'] = list3[key]
                databaseItem[coin]['p'] = list4[key]
                databaseItem[coin]['v'] = list5[key]
                databaseItem[coin]['tbv'] = list6[key]
                key = {'date': databaseItem['date']}

                storeOrUpdateResult(key, databaseItem)

while days_to_substract > 0:

    initial_date = start_at + timedelta(days=counter)
    end_date = initial_date + timedelta(days=1)
    start_time_item = time.time()
    print('!!! INITIAL DATE WORKING AT !!!', initial_date)

    for coin in targetCoin:

        start_time_coin = time.time()

        print(coin, baseCoin, '------>>>>')
        symbol = coin + baseCoin  # key/pair from market BTC

        data = get_historical_klines(symbol, '1m', str(initial_date), str(end_date))

        retryCounter = 0
        # retry 1
        if len(data) == 0:
            time.sleep(3)
            retryCounter += 1
            data = get_historical_klines(symbol, '1m', str(initial_date), str(end_date))

        # retry 2
        if len(data) == 0:
            time.sleep(3)
            retryCounter += 1
            data = get_historical_klines(symbol, '1m', str(initial_date), str(end_date))

        # retry 3
        if len(data) == 0:
            time.sleep(3)
            retryCounter += 1
            data = get_historical_klines(symbol, '1m', str(initial_date), str(end_date))

        # if retryCounter == 3:
        #     exit()

        result = {}
        aggregate = []

        if len(data) == 0:
            print('no data')
            continue

        first_item_ever = datetime.utcfromtimestamp(data[0][0] / 1000.0)
        first_item_ever = first_item_ever.replace(second=0, microsecond=0)

        if first_item_ever != initial_date and isFirstItem:
            raise RuntimeError('First minute does not exist, retry more in the past: at', first_item_ever)

        isFirstItem = False

        for item in data:

            date = datetime.utcfromtimestamp(item[0]/1000.0)
            date = date.replace(second=0, microsecond=0)

            ###             ALERT           ###
            ###             ALERT           ###
            ### this will only work for minutely capturing ###
            ### meant to replace missings for copies of the previous ###
            ### TODO replace minutes per hours in case of a change ###
            ###             ALERT           ###
            ###             ALERT           ###

            if lastStoredDate:
                lastStoredResultDate = lastStoredDate
                lastStoredResultDatePlusOneMinute = lastStoredResultDate + timedelta(minutes=1)

                # print(date, lastStoredResultDatePlusOneMinute)
                # TODO FIX IT. for now: remove this minute and hour exception if there are any missings and recapture period manually
                if date != lastStoredResultDatePlusOneMinute \
                        and (lastStoredResultDatePlusOneMinute.minute != 1 and lastStoredResultDatePlusOneMinute.hour != 0): # particular exception

                    print('missing range...', date, lastStoredResultDatePlusOneMinute)

                    guessedDate = lastStoredResultDate + timedelta(days=3)
                    needsInterpolation.append({'init': lastStoredResultDate, 'end': guessedDate})

                    # generateMockData(lastStoredResultDate)

            serializeAndStore(item, coin)
            lastStoredDate = date
            # gc.collect()

        del data
        gc.collect()
        print("--- %s seconds per coin per day ---" % (time.time() - start_time_coin))

    print("--- %s day finished, daily iteration seconds ---" % (time.time() - start_time_item), 'from START AT - ', str(start_at))

    counter += 1
    days_to_substract -= 1

### THE MISSINGS DO NOT COINTAIN DATA, JUST MAKE A FIX FOR THE AI ####
for coin in targetCoin:
    interpolate(coin)

print("--- %s TOTAL seconds ---" % (time.time() - start_time))

