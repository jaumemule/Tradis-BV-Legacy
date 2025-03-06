"use strict";

const coinsPricesModel = require('../models/coinsPrices');
const exchangeRatesRepository = require('../infra/exchangeRatesRepository');
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {
    exchangeRates : function(req, res, next){

        if (
            req.params.baseCoin !== 'USDT' 
            && req.params.baseCoin !== 'EUR'
        ) {
            return res.status(404).send()
        }

        if (
            req.params.exchangeName !== 'binance'
            && req.params.exchangeName !== 'coinbasepro' 
        ) {
            return res.status(404).send()
        }

        let baseCoinCollection = req.params.exchangeName + '_' + req.params.baseCoin

        if (req.params.baseCoin === 'USDT') {
            baseCoinCollection = req.params.baseCoin
        }

        exchangeRatesRepository.exchangeRates(req.params.baseCoin, req.params.exchangeName, req.query.after, req.query.before, function(err, result) {
            if (err !== null) return res.status(404).send({ data: { code: 'data_not_found', message: err}});
            return res.status(200).send(result)
        })
    },
    getLastAggregation : function(req, res, next){
        let coinCollection = mongoose.model('BTC', coinsPricesModel, 'BTC');
 
        let query = coinCollection.findOne().sort({ field: 'asc', _id: -1 }).limit(1)
        
        query.exec(function (err, doc) {
            if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
            if (err) return next(err);
            res.send(doc)
        });
    },

    // TODO not in use but might be useful
    _aggregateCoins : function(coin, req, res, next, cb){

        let coinCollection = mongoose.model(coin, coinsPricesModel, coin);
        
        let filter = {};

        if (req.query.after) filter = { date: { $gte: new Date(req.query.after) } }
        if (req.query.before) filter = { date: { $lte: new Date(req.query.before) } }

        let query = coinCollection.find(
            filter
        ).select('coin compareToCoin value date')
        .where('compareToCoin').equals(req.params.fromCoin)
        .limit(10000)
        .sort({'date':-1}); 

        query.exec(function (err, doc) {
            if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
            if (err) return next(err);
            cb(doc);
        });
    }
};
