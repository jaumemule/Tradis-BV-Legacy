const redisClient = require('../config/redisConnection').container
const ccxt = require('ccxt')

class ccxtIntegration {

    constructor(accountsConnections)
    {
        this.accountsConnections = accountsConnections
    }

    balancesFromExchange(cb, exchange) {
        let accountsConnections = this.accountsConnections

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            cb({error: 'account_not_found_or_not_active'})
            return
        }

        if (exchange.options && exchange.options.cached == true) {
            redisClient.get('balance_x_' + exchange.exchangeAccount, function(err, result){
                if(result === null) {
                    lookup(accountsConnections, exchange)
                } else {
                    console.log('from Redis', exchange.exchangeAccount)
                    cb(JSON.parse(result))
                }
            })
        } else {
            lookup(accountsConnections, exchange)
        }

        async function lookup (accountsConnections, exchange) {
            try {
                const balance = await accountsConnections[exchange.exchangeAccount].fetchBalance()
                let expirationInSeconds = 20
                let key = 'balance_x_' + exchange.exchangeAccount
                redisClient.set(key, JSON.stringify(balance), function(err, result) {
                    redisClient.expire(key, expirationInSeconds);
                    cb(balance)
                })
            } catch (e) {
                console.log(e)
                cb(null, e.message)
            }
        }
    }

    depositsFromExchange(cb, exchange) {
        let accountsConnections = this.accountsConnections

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            cb({error: 'account_not_found_or_not_active'})
            return
        }

        if (exchange.options && exchange.options.cached == true) {
            redisClient.get('balance' + exchange.exchangeAccount, function(err, result){
                if(result === null) {
                    lookup(accountsConnections, exchange)
                } else {
                    console.log('from Redis', exchange.exchangeAccount)
                    cb(JSON.parse(result))
                }
            })
        } else {
            lookup(accountsConnections, exchange)
        }

        async function lookup (accountsConnections, exchange) {
            try {
                const balance = await accountsConnections[exchange.exchangeAccount].fetchDeposits()
                let expirationInSeconds = 180
                let key = 'deposits' + exchange.exchangeAccount
                redisClient.set(key, JSON.stringify(balance), function(err, result) {
                    redisClient.expire(key, expirationInSeconds);
                    cb(balance)
                })
            } catch (e) {
                console.log(e)
                cb(null, e.message)
            }
        }
    }
    
    withdrawalsFromExchange(cb, exchange) {
        let accountsConnections = this.accountsConnections

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            cb({error: 'account_not_found_or_not_active'})
            return
        }

        if (exchange.options && exchange.options.cached == true) {
            redisClient.get('balance' + exchange.exchangeAccount, function(err, result){
                if(result === null) {
                    lookup(accountsConnections, exchange)
                } else {
                    console.log('from Redis', exchange.exchangeAccount)
                    cb(JSON.parse(result))
                }
            })
        } else {
            lookup(accountsConnections, exchange)
        }

        async function lookup (accountsConnections, exchange) {
            try {
                const balance = await accountsConnections[exchange.exchangeAccount].fetchWithdrawals()
                let expirationInSeconds = 180
                let key = 'deposits' + exchange.exchangeAccount
                redisClient.set(key, JSON.stringify(balance), function(err, result) {
                    redisClient.expire(key, expirationInSeconds);
                    cb(balance)
                })
            } catch (e) {
                console.log(e)
                cb(null, e.message)
            }
        }
    }    

    tradesFromExchange(cb, exchange) {
        let accountsConnections = this.accountsConnections

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            cb({error: 'account_not_found_or_not_active'})
            return
        }

        if (exchange.options && exchange.options.cached == true) {
            redisClient.get('trades' + exchange.exchangeAccount, function(err, result){
                if(result === null) {
                    lookup(accountsConnections, exchange)
                } else {
                    console.log('from Redis', exchange.exchangeAccount)
                    cb(JSON.parse(result))
                }
            })
        } else {
            lookup(accountsConnections, exchange)
        }

        async function lookup (accountsConnections, exchange) {
            try {
                const balance = await accountsConnections[exchange.exchangeAccount].fetchTrades('LTC/BTC')
                let expirationInSeconds = 180
                let key = 'deposits' + exchange.exchangeAccount
                redisClient.set(key, JSON.stringify(balance), function(err, result) {
                    redisClient.expire(key, expirationInSeconds);
                    cb(balance)
                })
            } catch (e) {
                console.log(e)
                cb(null, e.message)
            }
        }
    }

    buyFromExchange(callbackToController, exchange) {

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            callbackToController({error: 'account_not_found_or_not_active'})
            return
        }

        let orders = exchange.orders;
        let exchangeAccount = exchange.exchangeAccount;
        let ordersResult = [];
        let accountsConnections = this.accountsConnections

        function buy(accountsConnections, order, cb) {
            let market = order.baseCurrency + '/' + order.targetCurrency;

            (async () => {
                try {
                    const result = await accountsConnections[exchangeAccount].createMarketBuyOrder(market, order.quantity)
                    cb(result, null, market)
                } catch (e) {
                    cb(e.message, e.constructor.name, market, order.quantity)
                }
            })()
        }

        let counter = 0;
        for (let index = 0; index < orders.length; index++) {
            let result = {};

            buy(accountsConnections, orders[index], function (data, err, market, quantity) {
                console.log(err)
                if (err !== null) {
                    result[market] = { success: false, quantity: quantity, error: err, message: data }
                } else {
                    result[market] = { success: true, quantity: quantity }
                }

                ordersResult.push(result)
                counter++;

                if (counter == orders.length) {
                    callbackToController(ordersResult)
                }
            })
        }
    }

    // ************************************************************************
    // ***************************   SELL PART    *****************************
    // ************************************************************************

    sellFromExchange(callbackToController, exchange) {

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            callbackToController({error: 'account_not_found_or_not_active'})
            return
        }

        let orders = exchange.orders;
        let exchangeAccount = exchange.exchangeAccount;
        let ordersResult = [];
        let accountsConnections = this.accountsConnections

        function sell(accountsConnections, order, cb) {
            let market = order.baseCurrency + '/' + order.targetCurrency;
            
            (async () => {
                try {
                    const result = await accountsConnections[exchangeAccount].createMarketSellOrder(market, order.quantity)
                    cb(result, null, market)
                } catch (e) {
                    cb(e.message, e.constructor.name, market, order.quantity)
                }
            })()
        }

        let counter = 0;
        for (let index = 0; index < orders.length; index++) {
            let result = {};

            sell(accountsConnections, orders[index], function (data, err, market, quantity) {
                console.log(err)
                if (err !== null) {
                    result[market] = { success: false, quantity: quantity, error: err, message: data }
                } else {
                    result[market] = { success: true, quantity: quantity }
                }

                ordersResult.push(result)
                counter++;

                if (counter == orders.length) {
                    callbackToController(ordersResult)
                }
            })
        }
    }

    openOrdersFromExchange(callbackToController, exchange) {

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            callbackToController({error: 'account_not_found_or_not_active'})
            return
        }

        let orders = exchange.orders;
        let ordersResult = [];
        let exchangeAccount = exchange.exchangeAccount;
        let accountsConnections = this.accountsConnections

        function openOrders(accountsConnections, order, cb) {

            let market = order.market;

            if (order.market) {
                (async () => {
                    try {
                        const result = await accountsConnections[exchangeAccount].fetchOpenOrders(market)
                        cb(result, null, market)
                    } catch (e) {
                        cb(e.message, e.constructor.name, market)
                    }
                })()
            } else {
                cb('Market not specified', 'undefinedMarket', null)
            }
        }

        let counter = 0;
        for (let index = 0; index < orders.length; index++) {
            let result = {};

            openOrders(accountsConnections, orders[index], function (data, err, market) {
                
                if (err !== null) {
                    result[market] = { success: false, error: err, data: data }
                    // only return something if there is something to say
                    ordersResult.push(result)
                } else if (data.length > 0) {
                    result[market] = { success: false, error: err, data: data }
                    ordersResult.push(result)
                }

                counter++;

                if (counter == orders.length) {
                    callbackToController(ordersResult)
                }
            })
        }
    }

    cancelOpenOrdersForSpecificMarketFromExchange(callbackToController, exchange) {

        if (!this.accountsConnections.hasOwnProperty(exchange.exchangeAccount)) {
            callbackToController({error: 'account_not_found_or_not_active'})
            return
        }

        let orders = exchange.orders;
        let exchangeAccount = exchange.exchangeAccount;

        (async () => {
            try {
                const result = await this.accountsConnections[exchangeAccount].cancelOrder(orders.id, orders.market)
                let finalResult = { success: true, order: result }
                callbackToController(finalResult)
            } catch (e) {
                let finalResult = { success: false, message: e.message, error: e.constructor.name }
                callbackToController(finalResult)
            }
        })()
    }

    // very MVP
    exchangeRatesOHLCV(callbackToController, exchange, untilTimestamp, fromTimestamp, symbol) {
        // exchange = ccxt[exchange]
        // ohlcvs = exchange.fetch_ohlcv(symbol, '1m', since=fromTimestamp, limit=3)

        // callbackToController(ohlcvs)

        return
    }
}

module.exports = ccxtIntegration;
