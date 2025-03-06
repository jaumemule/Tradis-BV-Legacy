from src.simulate import Worker
import sys, getopt
import datetime

try:
    opts, args = getopt.getopt(sys.argv[1:], 'f:u:s:t:lm:stop,jump,take, whaleup, whaledown, whalelookup, candle, strategy, softStrategyLock, extendLockUntilHardPrediction, help', ['from=', 'until=', 'slack', 'tradingBotsEnabled', 'lockingMinutes=', 'stoploss=', 'jumptomarket=', 'takeprofit=', 'whaleUpPercent=', 'whaleDownPercent=', 'whaleMinuteLookup=', 'candleSize=', 'strategyName=', 'ignoreStrategyLockOnHardSignal', 'extendLockUntilHardPrediction', 'help'])
except getopt.GetoptError:
    print('---- errors while executing ---- check your argument list and try again',  getopt.GetoptError)
    sys.exit(2)

startAt = None
untilDate = None
sendToSlack = None
lockingMinutes = None
stoploss = False
jumptomarket = False
whaleDownPercent = None
whaleUpPercent = None
whaleMinuteLookup = None
takeprofit = False
lockStrategyAlsoForTradingBot = False
tradingBotsEnabled = False
candleSize = None
strategyName = None
ignoreStrategyLockOnHardSignal = False
extendLockUntilHardPrediction = False

for opt, arg in opts:
    if opt in ('-h', '--help'):
        print("run this as an example: ", "python __simulate__.py --from=\"2020-03-01 00:50\" --until=\"2020-06-15 23:50\" --stoploss 1000 --jumptomarket 1000 --takeprofit 5 --lockingMinutes 0 --strategyName ploutos --candleSize 240 --tradingBotsEnabled --ignoreStrategyLockOnHardSignal --extendLockUntilHardPrediction --slack")
        sys.exit(2)
    elif opt in ('-f', '--from'):
        startAt = arg
        startAt = datetime.datetime.strptime(str(startAt) + ':00', '%Y-%m-%d %H:%M:%S')
    elif opt in ('-u', '--until'):
        untilDate = arg
        untilDate = datetime.datetime.strptime(str(untilDate) + ':00', '%Y-%m-%d %H:%M:%S')
    elif opt in ('-stop', '--stoploss'):
        stoploss = float(arg) * -1
    elif opt in ('-jump', '--jumptomarket'):
        jumptomarket = float(arg)
    elif opt in ('-take', '--takeprofit'):
        takeprofit = float(arg)
    elif opt in ('-whaleup', '--whaleUpPercent'):
        whaleUpPercent = float(arg)
    elif opt in ('-whaledown', '--whaleDownPercent'):
        whaleDownPercent = float(arg)
    elif opt in ('-whalelookup', '--whaleMinuteLookup'):
        whaleMinuteLookup = float(arg)
    elif opt in ('-lm', '--lockingMinutes'):
        lockingMinutes = int(arg)
    elif opt in ('-t', '--tradingBotsEnabled'):
        tradingBotsEnabled = True
    elif opt in ('-softStrategyLock', '--ignoreStrategyLockOnHardSignal'):
        ignoreStrategyLockOnHardSignal = True
    elif opt in ('-extendLockUntilHardPrediction', '--extendLockUntilHardPrediction'):
        extendLockUntilHardPrediction = True
    elif opt in ('-s', '--slack'):
        sendToSlack = True
    elif opt in ('-candle', '--candleSize'):
        candleSize = int(arg)
    elif opt in ('-strategy', '--strategyName'):
        strategyName = arg
    else:
        print('incorrect argument list')
        sys.exit(2)


worker = Worker(
    'simulation',
    startAt,
    untilDate,
    sendToSlack,
    lockingMinutes,
    stoploss,
    jumptomarket,
    whaleDownPercent,
    whaleUpPercent,
    whaleMinuteLookup,
    takeprofit,
    lockStrategyAlsoForTradingBot,
    tradingBotsEnabled,
    candleSize,
    strategyName,
    ignoreStrategyLockOnHardSignal,
    extendLockUntilHardPrediction,
)
worker.fire()
