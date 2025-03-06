"use strict";

const AccountTrades = require('../models/accountTrades')
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {

    insertAccountResult : function(
        balanceState,
        isStartingPoint = true,
        callback
    ){
        let AccountTradesInstance = new AccountTrades();
        AccountTradesInstance.rates = balanceState.exchangeRate
        AccountTradesInstance.balances = balanceState.activeBalancesForStrategyDict
        AccountTradesInstance.totals = balanceState.totalBalanceInEveryCoinDict
        AccountTradesInstance.baseCoin = balanceState.baseCoin
        AccountTradesInstance.exchange = balanceState.exchange
        AccountTradesInstance.resultCalculationStartingPoint = isStartingPoint
        AccountTradesInstance.signals = balanceState.signals

        AccountTradesInstance.source = 'API'
        AccountTradesInstance.action = 'Update account state'

        AccountTradesInstance._strategy = balanceState.strategyId
        AccountTradesInstance._user = balanceState.userId
        AccountTradesInstance._account = balanceState.accountId

        // for legacy reasons, if strategy is procyon...
        if ('USDT' in balanceState.totalBalanceInEveryCoinDict) {
            AccountTradesInstance.totalUSDBeforeTrading = balanceState.totalBalanceInEveryCoinDict['USDT']
        }

        if ('BTC' in balanceState.totalBalanceInEveryCoinDict) { // TODO add strategy Ids in production to filter
            AccountTradesInstance.totalBtcBeforeTrading = balanceState.totalBalanceInEveryCoinDict['BTC']
            AccountTradesInstance.BTCvalue = balanceState.exchangeRate['BTC']['p']
            AccountTradesInstance.USDvalue = 1
        }

        AccountTradesInstance.save(function(err, result) {
            if (err || result === null) {
                return callback('Could not insert new account balance')
            } else {
                return callback(null, result)
            }
        })
    }
}