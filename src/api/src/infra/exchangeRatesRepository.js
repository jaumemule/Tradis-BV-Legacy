"use strict";

const coinsPricesModel = require('../models/coinsPrices')
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {

    exchangeRates : function(baseCoin, exchangeName, since = null, until = null, callback){

        // legacy reasons
        if (
            baseCoin!== 'USDT' 
            && baseCoin !== 'EUR'
        ) {
            return callback('Coin not Found', null)
        }

        if (
            exchangeName !== 'binance'
            && exchangeName !== 'coinbasepro' 
        ) {
            return callback('Exchange not Found', null)
        }

        let baseCoinCollection = exchangeName + '_' + baseCoin

        if (baseCoin === 'USDT') {
            baseCoinCollection = baseCoin
        }

        // TODO generalize and sanitise request
        let coinCollection = mongoose.model(baseCoinCollection, coinsPricesModel, baseCoinCollection);

        let filter = {};

        if (since !== null) since = new Date(since)
        if (until !== null) until = new Date(until) 

        if (since !== null) filter = { date: { $gte: since } }
        if (until !== null) filter = { date: { $lte: until } }

        let query = coinCollection.find(filter)

        query.exec(function (err, doc) {
            if (doc === null) return callback('Data not found', null)
            if (err !== null) return callback('Error retrieving exchange rates', null);

            doc.sort(function(a,b){
                // Turn your strings into dates, and then subtract them
                // to get a value that is either negative, positive, or zero.
                return new Date(a.date) - new Date(b.date);
            });

            return callback(null, doc)
        });
    }
}