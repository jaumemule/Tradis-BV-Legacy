"use strict";

const async = require('async');
const accountsInMemoryContainer = require('../infra/accountsInMemoryContainer')

const ccxtIntegration = require('../exchanges/ccxtIntegration')
const ExchangeFactory = require('../exchanges/factory')

let self = module.exports = {

    buy : function(req, res, next){

        // this will request to all the exchanges in parallel and merge the results
        // it instantiates a factory per each exchange, that unifies the implementation
        // and maps the results to an standarised response for the output
        // the factory per each exchange will also send multiple requests asyncronously
        
        let tasks = {}

        console.log('buy', req.body)

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, value.orders)        
                    Factory.buy(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },
    sell : function(req, res, next){

        let tasks = {}

        console.log('sell: ', req.body)

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, value.orders)        
                    Factory.sell(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },
    balances : function(req, res, next){
        let tasks = {}

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, null, {cached: req.query.cached})        
                    Factory.balances(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },
    deposits : function(req, res, next){
        let tasks = {}

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, null, {cached: req.query.cached})        
                    Factory.deposits(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },
    withdrawals : function(req, res, next){
        let tasks = {}

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, null, {cached: req.query.cached})        
                    Factory.withdrawals(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },
    trades : function(req, res, next){
        let tasks = {}

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, null, {cached: req.query.cached})        
                    Factory.trades(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },
    openOrders : function(req, res, next)
    {
        let tasks = {}

        console.log('open orders: ', req.body)

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, value.orders)        
                    Factory.openOrders(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
 
    },
    cancelOrders : function(req, res, next)
    {
        let tasks = {}

        req.body.forEach(function(value){
            let executableFunction = function(callback) {
                let Factory = new ExchangeFactory(accountsInMemoryContainer, value.exchangeName, value.account, value.orders)        
                    Factory.cancelOrders(function(data){
                        callback(null, {result: data})
                })
            }

            tasks[value.account] = executableFunction
        })

        async.parallel(tasks, function(err, results) {
            res.send(results) 
        })
    },

    // very MVP
    exchangeRates : function(req, res, next)
    {
        ccxtIntegrationService = new ccxtIntegration({})
        
        untilTimestamp = datetime.utcnow() - timedelta(minutes=1)
        fromTimestamp = int((fromdate - datetime(1970, 1, 1)).total_seconds() * 1000)

        ccxtIntegrationService.exchangeRatesOHLCV(
            'binance',
            untilTimestamp,
            fromTimestamp,
            symbol,
        )

    }
}
