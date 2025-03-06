"use strict";

// DEPRECATED CLASS, SEE ACCOUNTS RESULTS CONTROLLER
// DEPRECATED CLASS, SEE ACCOUNTS RESULTS CONTROLLER
// DEPRECATED CLASS, SEE ACCOUNTS RESULTS CONTROLLER

const strategiesModel = require('../models/strategies');
const profitabilityModel = require('../models/profitability');
const database = require('../config/database');
const redisClient = require('../config/redisConnection').container
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {

    results : function(req, res)
    {
        strategiesModel.findOne({strategyName : req.params.strategyName}).exec(function (err, strategy){
            if (strategy === undefined || strategy === null) {
                return res.status(404).send({message: 'strategy does not exist'})
            } else {

                let redisKey = 'strategy_plot_' + strategy['_id']

                redisClient.get(redisKey, function(err, result){
                    if(result === null) {
                        console.log('performing lookup for strategy plots')
                        fetchStrategyPerformanceFromLeadAccount (redisKey, function (result) {
                            return res.send(result)
                        })
                    } else {
                        console.log('from Redis')
                        return res.send(JSON.parse(result))
                    }
                })
            }

            async function fetchStrategyPerformanceFromLeadAccount(redisKey, cb)
            {
                let collectionName = undefined
                switch (req.params.strategyName) {
                    case 'procyon':
                        collectionName = 'transactions_procyon_USDT_real_money'
                        break;

                    case 'procyon_pure':
                        collectionName = 'transactions_procyon_pure_real_money'
                        break;

                    case 'ploutos':
                        collectionName = 'transactions_ploutos_lead'
                        break;

                    default:
                        collectionName = undefined

                }

                if (collectionName === undefined) {
                    return res.status(404).send()
                }

                let collection = mongoose.model(collectionName, profitabilityModel, collectionName);
                queryWithCollection(collection)

                // TODO add filter by before and after
                function queryWithCollection(collection) {

                    let query = collection.aggregate(
                        [
                            {
                                $project: {
                                    hour:{$hour:"$at"}, at: 1, rates: 1, totals: 1, _id: 0
                                }
                            }, 
                            {
                                $match:
                                {
                                    hour:{
                                        "$in" : [0,4,8,12,16,20] // to speed up results
                                    },
                                    at : {
                                        $gt : new Date("2020-10-18T20:51:24.190Z") // new format
                                    }
                                }
                            },
                        ]
                    )

                    query.exec(function (err, doc) {
                        if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
                        if (err) return next(err);

                        let profit = {}
                        let balance = {}
                        let range = {}

                        let usedCoinsInStrategyList = Object.keys(strategy.exchangeMarkets);
                        let coinsToComputeWithoutBaseCoinList = usedCoinsInStrategyList.filter(item => item !== strategy.baseCoin)

                        for (let coinIndex in usedCoinsInStrategyList) {
                            let coin = usedCoinsInStrategyList[coinIndex]

                            let initialBalance = doc[0].totals[coin]
                            let finalBalance = doc[doc.length - 1].totals[coin]

                            profit[coin] = ((finalBalance - initialBalance) / initialBalance) * 100
                            profit[coin] = profit[coin].toFixed(2) + '%'

                            range['from'] = doc[0].at
                            range['until'] = doc[doc.length - 1].at

                            balance[coin] = {}
                            balance[coin]['initial'] = initialBalance
                            balance[coin]['final'] = finalBalance
                        }

                        let tradingPairs = []
                        for (let targetCoin in strategy.exchangeMarkets) {
                            if (targetCoin !== strategy['baseCoin']) {
                                let pair = targetCoin + '/' + strategy.exchangeMarkets[targetCoin].market;
                                tradingPairs.push(pair);
                            }
                        }


                        let marketBenchmarks = {}
                        for (let targetCoin in strategy.exchangeMarkets) {
                            if (targetCoin !== strategy['baseCoin']) {    
                                let pairEndPrice = doc[doc.length - 1]['rates'][targetCoin]['p']
                                let pairInitialPrice = doc[0]['rates'][targetCoin]['p']

                                let result = ((pairEndPrice - pairInitialPrice) / pairInitialPrice) * 100

                                marketBenchmarks[targetCoin] = result.toFixed(2) + '%'
                            }
                        }
                        
                        let stats = {
                            baseCoin: strategy['baseCoin'],
                            tradingPairs,
                            targetCoins: coinsToComputeWithoutBaseCoinList,
                            profit,
                            range,
                            balance,
                            marketBenchmarks,
                        }

                        // remove unnecessary noise to speed up transfer
                        Object.keys(doc).map(function(key, index) {
                            delete(doc[key]['_id'])
                            delete(doc[key]['rates'][strategy.baseCoin])
                            delete(doc[key]['hour'])
                            coinsToComputeWithoutBaseCoinList.forEach(function(targetCoin, index) {
                                doc[key]['rates'][targetCoin] = doc[key]['rates'][targetCoin]['p']
                            })
                        });

                        let data = {
                            stats,
                            plot: doc
                        }

                        let expirationInSeconds = 120 // expires every 2h
                        redisClient.set(redisKey, JSON.stringify(data), function(err, result) {
                            redisClient.expire(redisKey, expirationInSeconds);
                            cb(data)
                        })
                    });
                }
            }
        })
    },

    // DEPRECATED, in use for graph page
    profitabilityPerStrategy : function(req, res, next){
        const doc = new strategiesModel(req.body);

        let query = strategiesModel.findOne().where('strategyName').equals(req.params.strategyName).exec(function (err, strategy){
            if (err) return next(err);
            if (strategy === null) {
                res.status(404).send({message: 'strategy does not exist'})
            } else {
                
                let nomenclature = database.nomenclaturePerStrategy(strategy)
                let collectionName = 'transactions_' + nomenclature
                let collection = mongoose.model(collectionName, profitabilityModel, collectionName);
                queryWithCollection(collection)

                // TODO add filter by before and after
                function queryWithCollection(collection) {
                    let query = collection.find()
                    .select('totalBtcBeforeTrading totalUSDBeforeTrading at USDvalue BTCvalue')
                    .sort({ field: 'asc', _id: -1 }).limit(1000)
            
                    query.exec(function (err, doc) {
                        if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
                        if (err) return next(err);
                        res.send(doc)
                    });
                }
            }
        })
    },

    // DEPRECATED, currently maybe not in use
    percentageOfProfitability: function(req, res, next) {
        // TODO NOW LET'S HARDCODE THE STRATEGY COLLECTION

        const doc = new strategiesModel(req.body);

        let query = strategiesModel.findOne().where('strategyName').equals(req.params.strategyName).exec(function (err, docResult){
            if (err) return next(err);
            if (docResult === null) {
                res.status(404).send({message: 'strategy does not exist'})
            } else {

                let collectionName = ''
                // TODO remove this hardcoded logic
                // STANDARISE THIS FOR FUCK SAKE
                if (req.params.strategyName === 'keras_1') {
                    let collectionName = 'transactions_keras_real_money'
                    let collection = mongoose.model(collectionName, profitabilityModel, collectionName);
                    queryWithCollection(collection)
                } else if (req.params.strategyName === 'real_money_testing') {
                    let collectionName = 'sandbox_transactions_real_money_testing'
                    let collection = mongoose.model(collectionName, profitabilityModel, collectionName);
                    queryWithCollection(collection)
                } else {
                    res.send([])
                }

                function queryWithCollection(collection) {

                    let filter = {}

                    // we take results from 3h ago and pick up the newest one
                    var backup = new Date()
                    var now = new Date()
                    backup.setHours(now.getHours() - 12);

                    filter = { 'at': { $gte: backup, $lte: now } }
                    let query = collection.find(
                        filter
                    )
                    .select('totalBtcBeforeTrading totalUSDBeforeTrading at')
                    .sort({ date: -1 }).limit(100)
            
                    query.exec(function (err, doc) {

                        if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
                        if (err) return next(err);

                        let filter = {}

                        var timeAgo = new Date();
                        var timeAgoBackup = new Date();
                        timeAgo.setDate(timeAgo.getDate() - 1);
                        timeAgoBackup.setDate(timeAgoBackup.getDate() - 1);
                        timeAgoBackup.setHours(timeAgoBackup.getHours() + 12);
                        
                        filter = { 'at': { $gte: timeAgo, $lte: timeAgoBackup } }
                        let query = collection.find(
                            filter
                        )
                        .select('totalBtcBeforeTrading totalUSDBeforeTrading at')
                        .sort({ date: 1 }).limit(100)
                
                        query.exec(function (err, oldDoc) {

                            if (oldDoc == null || oldDoc.length === 0) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
                            if (err) return next(err);

                            let timeAgoDocAmount = doc.length === 0 ? 0 : oldDoc[0]['totalUSDBeforeTrading']

                            let recentDocAmount = doc[0]['totalUSDBeforeTrading']
                            let percentage = (recentDocAmount - timeAgoDocAmount) / timeAgoDocAmount * 100
                            
                            res.send({percentage: percentage.toFixed(2)})
                        });
                    });
                }
            }
        })
    }
};
