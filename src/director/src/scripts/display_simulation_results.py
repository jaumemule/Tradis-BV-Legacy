## this is meant to remove all the extra collections present in mongo that are not interesting
## for example, test collections or simulation collections
import sys

sys.path.append('/usr/app/src/director')

import pymongo
import os

from src.domain.Simulation import Simulation

localMongoConnection = os.getenv('MONGO_CONNECTION')
if not localMongoConnection:
    localMongoConnection = 'mongodb://localhost:27017/'

localMongoConnection = 'mongodb://xxxxxxx/aggregated'

localClient = pymongo.MongoClient(localMongoConnection)
localDb = localClient.aggregated

simulations = localDb['simulations_aggregation']


result = simulations.find()

aggregation = {}

for doc in result:
    key = 'from ' + str(str(doc['startAt']) + ' to ' + str(doc['untilDate']))

    strategyId = doc['strategyId'] if 'strategyId' in doc else None
    startAt = doc['startAt'] if 'startAt' in doc else None
    untilDate = doc['untilDate'] if 'untilDate' in doc else None
    results = doc['result'] if 'result' in doc else None
    lockingMinutes = doc['lockingMinutes'] if 'lockingMinutes' in doc else None
    stoploss = doc['stoploss'] if 'stoploss' in doc else None
    jumptomarket = doc['jumptomarket'] if 'jumptomarket' in doc else None
    whaleDownPercent = doc['whaleDownPercent'] if 'whaleDownPercent' in doc else None
    whaleUpPercent = doc['whaleUpPercent'] if 'whaleUpPercent' in doc else None
    whaleMinuteLookup = doc['whaleMinuteLookup'] if 'whaleMinuteLookup' in doc else None
    takeprofit = doc['takeprofit'] if 'takeprofit' in doc else None
    lockStrategy = doc['lockStrategy'] if 'lockStrategy' in doc else None
    tradingBotsEnabled = doc['tradingBotsEnabled'] if 'tradingBotsEnabled' in doc else None
    candleSize = doc['candleSize'] if 'candleSize' in doc else None
    strategyName = doc['strategyName'] if 'strategyName' in doc else None
    ignoreStrategyLockOnHardSignal = doc['ignoreStrategyLockOnHardSignal'] if 'ignoreStrategyLockOnHardSignal' in doc else None
    extendLockUntilHardPrediction = doc['extendLockUntilHardPrediction'] if 'extendLockUntilHardPrediction' in doc else None

    simulation = Simulation(
        strategyId,
        startAt,
        untilDate,
        results,
        lockingMinutes,
        stoploss,
        jumptomarket,
        whaleDownPercent,
        whaleUpPercent,
        whaleMinuteLookup,
        takeprofit,
        lockStrategy,
        tradingBotsEnabled,
        candleSize,
        strategyName,
        ignoreStrategyLockOnHardSignal,
        extendLockUntilHardPrediction,
    )

    serialized = simulation.toObject()

    # order by prio
    if key not in aggregation:
        aggregation[key] = []

    if (len(aggregation[key]) > 0) and (float(serialized['result']['BTC']) > float(aggregation[key][0][0]['result']['BTC'])):
        aggregation[key].insert(0, [serialized, simulation.toString()])
    else:
        aggregation[key].append([serialized, simulation.toString()])

output = ''
for key, period in aggregation.items():
    for position, doc in enumerate(period):

        if position == 0:

            output += '------------------------------------------------------------' + "\n"
            output += '-----   '+key+'   -----' + "\n"
            output += '------------------------------------------------------------' + "\n"

        output += doc[1] + "\n"

    output += '------------------------------------------------------------' + "\n"
    output += '-----------------------   END    ---------------------------' + "\n"
    output += '------------------------------------------------------------' + "\n"

with open(os.path.join('src', 'scripts', 'simulation.txt'), 'w') as text_file:
    print(f"{output}", file=text_file)