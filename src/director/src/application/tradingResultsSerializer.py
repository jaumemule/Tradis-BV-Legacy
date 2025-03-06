from typing import Tuple, Any, List, Union
from bson.objectid import ObjectId
from src.application.BalanceStateObject import BalanceStateObject

class TradingResultsSerializer:

    current_balances: object
    predictedCoinsWithCurrentCoinValue: list
    previousInvestmentWithCurrentCoinValue: list
    traderIntendedToSell: Union[List[Any], Any]
    previousCoinsWithMoney: Union[List[Any], Any]
    traderIntendedToBuy: Union[List[Any], Any]
    AIpredictions: Union[List[Any], Any]
    repeatedPredictionsRegardingPreviousOne: Union[List[Any], Any]
    predictionResults: list
    sell_conclusion: Tuple[str]
    BTCvalue: Tuple[Any]
    BNBvalue: Tuple[Any]
    USDvalue: Tuple[Any]
    totalBnbBeforeTrading: Tuple[Any]
    totalUSDBeforeTrading: Tuple[Any]
    totalBtcBeforeTrading: Tuple[Any]
    at: Tuple[str]
    bought: Tuple[object]

    def __init__(self):
        pass

    def createResults(
            self,
            sell: list,
            buy: list,
            accountsContainer,
            accountName,
            at,
            source,
            isStrategyLockedToTrade,
            strategy
    ) -> 'TradingResultsSerializer':
        """

        :type transactionMessages: object
        """
        self.bought = buy
        self.sold = sell
        self.source = source

        self.at = at

        self.accountName = accountName
        self.isStrategyLockedToTrade = isStrategyLockedToTrade
        self.strategy = strategy

        self.transactionMessages = accountsContainer.getResult(accountName, 'transactionMessages')

        self.totalBtcBeforeTrading = accountsContainer.getResult(accountName, 'totalBeforeTradingBtc')
        self.totalUSDBeforeTrading = accountsContainer.getResult(accountName, 'totalTUSDBeforeTrading')
        self.totalBnbBeforeTrading = accountsContainer.getResult(accountName, 'totalBnbBeforeTrading')
        self.USDvalue = accountsContainer.getResult(accountName, 'currentUSDMarketValue')
        self.BNBvalue = accountsContainer.getResult(accountName, 'currentBnbMarketValue')
        self.BTCvalue = accountsContainer.getResult(accountName, 'currentBtcMarketValue')

        self.accountsContainer = accountsContainer

        self.previousInvestmentWithCurrentCoinValue = accountsContainer.getResult(accountName, 'previousInvestmentWithCurrentCoinValue')
        self.predictedCoinsWithCurrentCoinValue = accountsContainer.getResult(accountName, 'predictedCoinsWithCurrentCoinValue')

        self.AIpredictions = accountsContainer.getResult(self.accountName, 'AIpredictions')
        self.repeatedPredictionsRegardingPreviousOne = accountsContainer.getResult(self.accountName, 'repeated')

        if self.AIpredictions:
            self.AIpredictions = list(self.AIpredictions)
            self.repeatedPredictionsRegardingPreviousOne = list(self.repeatedPredictionsRegardingPreviousOne)

        self.previousCoinsWithMoney = accountsContainer.getResult(self.accountName, 'previousCoinsWithMoney')
        self.traderIntendedToBuy = accountsContainer.getResult(self.accountName, 'wouldBuy')
        self.traderIntendedToSell = accountsContainer.getResult(self.accountName, 'wouldSell')


        return self

    def serialize(self, account, action, balanceStateObject: BalanceStateObject):

        predictions = self.AIpredictions

        if self.isStrategyLockedToTrade:
            action = 'locked_strategy'
            predictions = self.strategy['currentCoins']

        responseObject = {
            '_account': ObjectId(account['_id']),
            'bought': self.bought,
            'sold': self.sold,
            'at': self.at,
            'totalBtcBeforeTrading': self.totalBtcBeforeTrading,
            'totalUSDBeforeTrading': self.totalUSDBeforeTrading,
            'totalBnbBeforeTrading': self.totalBnbBeforeTrading,
            'USDvalue': self.USDvalue,
            'BNBvalue': self.BNBvalue,
            'BTCvalue': self.BTCvalue,
            'transactionMessages': self.transactionMessages,
            'AIpredictions': predictions,
            'source': self.source,
            'action': action,
            'repeatedPredictionsRegardingPreviousOne': self.repeatedPredictionsRegardingPreviousOne,
            'traderIntendedToBuy': self.traderIntendedToBuy,
            'traderIntendedToSell': self.traderIntendedToSell,
            'previousInvestmentWithCurrentCoinValue': self.previousInvestmentWithCurrentCoinValue,
            'predictedCoinsWithCurrentCoinValue': self.predictedCoinsWithCurrentCoinValue,
            'previousCoinsWithMoney': self.previousCoinsWithMoney,

            # new release
            'balances': balanceStateObject.get_balances(),
            'rates': balanceStateObject.get_rates(),
            'totals': balanceStateObject.get_totals(),
            'signals': predictions,
            'exchange': self.strategy['exchange'],
            '_strategy': balanceStateObject.get_strategy_id(),
            '_user': balanceStateObject.get_user_id(),

        }

        return responseObject

    def convertResultsIntoAfancyMessageString(self, method: str, basedCurrency, accountName, source: str) -> str:

        coinsWithMoney = str(self.previousCoinsWithMoney).strip('[]')

        conversionCoin = 'BTC'

        if 'ploutos' in self.strategy['strategyName']:
            conversionCoin = 'ETH'

        investedInMessage = ""
        if coinsWithMoney is not None:
            investedInMessage = " invested in " + coinsWithMoney

        if source == 'Stoploss':
            message = method + ": :octagonal_sign: Stoploss/Jump to market : *" +accountName+ "* :challenge_accepted: we have: " + str(self.totalBtcBeforeTrading) + " " + conversionCoin + ", same as " + str(round(self.totalUSDBeforeTrading, 2)) + " " + basedCurrency + investedInMessage + " \n"
        else:
            message = method + ": Running *" +accountName+ "* :challenge_accepted: we have: " + str(self.totalBtcBeforeTrading) + " " + conversionCoin + ", same as " + str(round(self.totalUSDBeforeTrading, 2)) + " " + basedCurrency + investedInMessage + " \n"

        if self.transactionMessages:
            for transactionMessage in self.transactionMessages:
                message += transactionMessage + "\n"

        AIpredictionsMessage = str(self.AIpredictions).strip('[]')

        if AIpredictionsMessage is not None:
            message += "AI predictions were: " + AIpredictionsMessage + "\n"

        if self.AIpredictions or self.repeatedPredictionsRegardingPreviousOne or self.previousCoinsWithMoney or self.traderIntendedToBuy or self.traderIntendedToSell:
            if len(self.traderIntendedToBuy) > 0:
                message += "intended to buy: " + str(self.traderIntendedToBuy).strip('[]') + "\n"
            if len(self.traderIntendedToSell) > 0:
                message += "and to sell: " + str(self.traderIntendedToSell).strip('[]') + "\n"

            if len(self.traderIntendedToBuy) == 0 and len(self.traderIntendedToSell) == 0:
                message += "we hold" + "\n"
        else:
            message += "We hold" + "\n"

        return message
