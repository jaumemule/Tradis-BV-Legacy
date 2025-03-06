from bson.objectid import ObjectId

class Simulation:

    def __init__(
        self,
        strategyId,
        startAt,
        untilDate,
        results: dict,
        lockingMinutes,
        stoploss=None,
        jumptomarket=None,
        whaleDownPercent=None,
        whaleUpPercent=None,
        whaleMinuteLookup=None,
        takeprofit=None,
        lockStrategy=None,
        tradingBotsEnabled=None,
        candleSize=None,
        strategyName=None,
        ignoreStrategyLockOnHardSignal=None,
        extendLockUntilHardPrediction=None,
    ):
        self.strategyId = strategyId
        self.startAt = startAt
        self.untilDate = untilDate
        self.results = results
        self.lockingMinutes = lockingMinutes
        self.stoploss = stoploss
        self.jumptomarket = jumptomarket
        self.whaleDownPercent = whaleDownPercent
        self.whaleUpPercent = whaleUpPercent
        self.whaleMinuteLookup = whaleMinuteLookup
        self.takeprofit = takeprofit
        self.lockStrategy = lockStrategy
        self.tradingBotsEnabled = tradingBotsEnabled
        self.candleSize = candleSize
        self.strategyName = strategyName
        self.ignoreStrategyLockOnHardSignal = ignoreStrategyLockOnHardSignal
        self.extendLockUntilHardPrediction = extendLockUntilHardPrediction

    def toObject(self) -> dict:

        result = {
            'result': self.results,
            'startAt': self.startAt,
            'untilDate': self.untilDate,
            'group':  str(self.startAt) + str(self.untilDate) + self.strategyName,
            'strategyId' : ObjectId(self.strategyId),
        }

        # optionals
        if self.whaleDownPercent != None:
            result['whaleDownPercent'] = self.whaleDownPercent
        if self.whaleUpPercent != None:
            result['whaleUpPercent'] = self.whaleUpPercent
        if self.stoploss != None and self.stoploss != False:
            result['stoploss'] = self.stoploss
        if self.jumptomarket != None and self.jumptomarket != False:
            result['jumptomarket'] = self.jumptomarket
        if self.whaleMinuteLookup != None and self.whaleMinuteLookup != False:
            result['whaleMinuteLookup'] = self.whaleMinuteLookup
        if self.takeprofit != None and self.takeprofit != False:
            result['takeprofit'] = self.takeprofit
        if self.lockStrategy != None:
            result['lockStrategy'] = self.lockStrategy
        if self.tradingBotsEnabled != None:
            result['tradingBotsEnabled'] = self.tradingBotsEnabled
        if self.candleSize != None:
            result['candleSize'] = self.candleSize
        if self.strategyName != None and self.strategyName != False:
            result['strategyName'] = self.strategyName
        if self.ignoreStrategyLockOnHardSignal != None and self.ignoreStrategyLockOnHardSignal != False:
            result['ignoreStrategyLockOnHardSignal'] = self.ignoreStrategyLockOnHardSignal
        if self.extendLockUntilHardPrediction != None and self.extendLockUntilHardPrediction != False:
            result['extendLockUntilHardPrediction'] = self.extendLockUntilHardPrediction
        if self.lockingMinutes != None and self.lockingMinutes != False:
            result['lockingMinutes'] = self.lockingMinutes

        return result

    def toString(self) -> str:

        result = str(self.startAt) + str(self.untilDate) + self.strategyName + "\n"

        if self.whaleDownPercent != None:
            result+= 'whaleDownPercent: ' + str(self.whaleDownPercent) + "\n"
        if self.whaleUpPercent != None:
            result+= 'whaleUpPercent: ' + str(self.whaleUpPercent) + "\n"
        if self.stoploss != None and self.stoploss != False:
            result+= 'stoploss: ' + str(self.stoploss) + "\n"
        if self.jumptomarket != None and self.jumptomarket != False:
            result+= 'jumptomarket: ' + str(self.jumptomarket) + "\n"
        if self.whaleMinuteLookup != None and self.whaleMinuteLookup != False:
            result+= 'whaleMinuteLookup: ' + str(self.whaleMinuteLookup) + "\n"
        if self.takeprofit != None and self.takeprofit != False:
            result+= 'takeprofit: ' + str(self.takeprofit) + "\n"
        if self.lockStrategy != None:
            result+= 'lockStrategy: ' + str(self.lockStrategy) + "\n"
        if self.tradingBotsEnabled != None:
            result+= 'tradingBotsEnabled: ' + str(self.tradingBotsEnabled) + "\n"
        if self.candleSize != None:
            result+= 'candleSize: ' + str(self.candleSize) + "\n"
        if self.strategyName != None and self.strategyName != False:
            result+= 'strategyName: ' + str(self.strategyName) + "\n"
        if self.ignoreStrategyLockOnHardSignal != None and self.ignoreStrategyLockOnHardSignal != False:
            result+= 'ignoreStrategyLockOnHardSignal: ' + str(self.ignoreStrategyLockOnHardSignal) + "\n"
        if self.extendLockUntilHardPrediction != None and self.extendLockUntilHardPrediction != False:
            result+= 'extendLockUntilHardPrediction: ' + str(self.extendLockUntilHardPrediction) + "\n"
        if self.lockingMinutes != None and self.lockingMinutes != False:
            result+= 'lockingMinutes: ' + str(self.lockingMinutes) + "\n"
        if self.results != None and self.results != False:
            result+= 'results: ' + str(self.results) + "\n"

        return result

