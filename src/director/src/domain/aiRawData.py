from bson.objectid import ObjectId

class AiRawData:

    def __init__(
        self,
        strategy_id,
    ):
        self.qvalues = None
        self.date = None
        self.observations = None
        self.strategy_id = strategy_id
        self.indicators = []
        self.state = None
        self.candles = None

    def toObject(self):

        return {
            "date" : self.date,
            "observations" : self.observations,
            "qvalues" : self.qvalues,
            "state" : self.state,
            "strategy" : {
                "strategyId": ObjectId(self.strategy_id),
                "candles" : self.candles
            }
        }

    def getIndicators(self):
        return self.indicators

    def addIndicators(self, indicators, candle: int):
        self.indicators.append({str(candle): indicators})

    def setDate(self, date):
        self.date = date

    def setQvalues(self, qvalues):
        self.qvalues = qvalues

    def setObservations(self, observations):
        self.observations = observations

    def setState(self, state):
        self.state = state

    def setCandles(self, candles: list):
        self.candles = candles
