"use strict";
const redisClient = require('../config/redisConnection').container

const Accounts = require('../models/accounts');
const AccountTrades = require('../models/accountTrades');
const tradesResults = require('../application/tradesResults');
const accountResultsRepository = require('../infra/accountResultsRepository');

let self = module.exports = {
    // this is used to calculate profit in portal
    // it will need iteration in the future. we will ignore withraws/deposits, etcetera
    firstBalance: function(req, res)
    {
        let accountId = req.params.accountId

        Accounts.findOne({ _id: accountId }, (err, account) => {
            // TODO log errors
            if (err) return res.status(500).send({error: 'Could not retrieve account'});
            if (!account) return res.status(404).send({error: 'Acccount not found'});

            let firstRecordEver = AccountTrades.findOne({
                '_account' : accountId,
                'totalUSDBeforeTrading' : {'$gt' : 0}
            }).sort({at: 1})

            let key = '1st_transaction_x_' + account.accountName
            let expirationInSeconds = 604800 // one week

            redisClient.get(key, function(err, result){
                if(result) {
                    console.log('from Redis', 'retrieved first transaction for', account.accountName)
                    return res.status(200).send(JSON.parse(result))
                } else {
                    firstRecordEver.exec(function (err, doc) {
                        if (doc === null) return res.status(404).send({ data: { code: 'data_not_found', message:'First trade not found'}});
                        if (err) return next(err);

                        let firstTrade = {
                            date: doc.at,
                            baseCoinAmount: doc.totalUSDBeforeTrading,
                            bitcoinAmount: doc.totalBtcBeforeTrading
                        }

                        redisClient.set(key, JSON.stringify(firstTrade), function(err, result) {
                            redisClient.expire(key, expirationInSeconds);
                            return res.status(200).send(firstTrade)
                        })
                    });
                }
            })
        })
    },

    // this is used to calculate profit in portal
    // it will take the first known state after user reset results
    // if never had reset, would fallback to firstBalance
    // this is also useful for keeping an historical of restarts

    // in case the balance is 0 for the first breaking point, will look forward
    // TODO introduce caching
    calculationStartingPoint: function(req, res)
    {
        let accountId = req.params.accountId

        Accounts.findOne({ _id: accountId }, (err, account) => {
            // TODO log errors
            if (err) return res.status(500).send({error: 'Could not retrieve account'});
            if (!account) return res.status(404).send({error: 'Acccount not found'});

            if (account.hasEverRestartedAccountProfit === false) {
                return self.firstBalance(req, res)
            }

            let firstRecordEver = AccountTrades.findOne({
                '_account' : accountId,
                'resultCalculationStartingPoint' : true,
            }).sort({at: -1})

            firstRecordEver.exec(function (err, firstBalanceOnBreakPoint) {
                if (firstBalanceOnBreakPoint === null) return res.status(404).send({ data: { code: 'data_not_found', message:'First trade not found'}});
                if (err) return next(err);

                // if balance was 0 at the moment it starts, look forward to find the next one
                if (firstBalanceOnBreakPoint.totalUSDBeforeTrading === 0) {

                    let nextRecordWithBalance = AccountTrades.findOne({
                        '_account' : accountId,
                        'at' : {"$gt" : firstBalanceOnBreakPoint.at},
                        'totalUSDBeforeTrading' : {'$gt' : 0}
                    }).sort({at: 1})

                    nextRecordWithBalance.exec(function (err, nextBalanceOnBreakPoint) {
                        if (nextBalanceOnBreakPoint === null) return res.status(404).send({ data: { code: 'data_not_found', message:'First trade not found'}});
                        if (err) return next(err);

                        return res.status(200).send(nextBalanceOnBreakPoint)

                    })

                } else {
                    return res.status(200).send(firstBalanceOnBreakPoint)
                }
            });
        })
    },

    // this replaces the previous calculation for Procyon, to show in portal
    getBalanceState: function(req, res)
    {
        Accounts.findOne({ _id: req.params.accountId }, (err, account) => {
            if (err) return status(500).send({message: err})
            if (account === null) return status(404).send({message: 'account not found'})

            let strategyId = account._strategy

            tradesResults.getBalanceState(req.params.accountId, strategyId, function(err, balanceState) {
                if (err) return res.status(500).send({message: err})
                if (balanceState) return res.status(200).send(balanceState)
            })
        })
    },

    // TODO this is setting from the last known result. has to create a new entry
    restartResultCalculationPoint: function(req, res)
    {
        Accounts.findOneAndUpdate(
            { _id: req.params.accountId },
            { $set: { hasEverRestartedAccountProfit : true } },
            { new: true },
            ( err, account ) => {
            if (err) {
                console.log("Something wrong when updating Accounts restartResultCalculationPoint!");
                return res.status(400).send({message: 'error on save'})
            } else {
                if (account === null) {
                    return res.status(404).send({})
                }
                tradesResults.getBalanceState(req.params.accountId, req.params.strategyId, function(err, balanceState) {
                    if (balanceState === null || err) return res.status(500).send({"message" : err})

                    accountResultsRepository.insertAccountResult(balanceState, true, function(err, result) {
                        if (err) console.log(err) // idempotent. although: TODO add monitoring and tracing
                        return res.status(201).send({message: "starting point was set"})
                    })
                })
            }
        });
    },
};
