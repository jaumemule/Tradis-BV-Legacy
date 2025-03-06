"use strict";
const binance = require('./binance')
const coinbasepro = require('./coinbasepro')
const ccxtIntegration = require('./ccxtIntegration')
const exhangesList = {binance, coinbasepro};

class Factory {

    constructor(accountsInMemoryContainer, exchange, exchangeAccount = 'default', orders = null, options = {})
    {
        let accountsConnections = accountsInMemoryContainer.connections()

        let ccxtIntegrationInstance = new ccxtIntegration(
            accountsConnections
        )

        this.request = { exchange: new exhangesList[exchange](
            this,
            orders,
            exchangeAccount,
            ccxtIntegrationInstance,
            options
        ), factory: this};
    };

    // TODO add a check to see if the account exists in the list
    __guardFromUnknownAccounts()
    {

    }

    buy(cb) 
    {
        return this.request.exchange.buy(function(data){
            cb(data)
        });
    }

    sell(cb) 
    {
        return this.request.exchange.sell(function(data){
            cb(data)
        });
    }

    balances(cb) 
    {
        return this.request.exchange.balances(function(data){
            cb(data)
        });
    }
    
    deposits(cb) 
    {
        return this.request.exchange.deposits(function(data){
            cb(data)
        });
    }
    
    withdrawals(cb) 
    {
        return this.request.exchange.withdrawals(function(data){
            cb(data)
        });
    }

    trades(cb) 
    {
        return this.request.exchange.trades(function(data){
            cb(data)
        });
    }
    
    openOrders(cb)
    {
        return this.request.exchange.openOrders(function(data){
            cb(data)
        });
    }

    cancelOrders(cb)
    {
        return this.request.exchange.cancelOpenOrdersForSpecificMarket(function(data){
            cb(data)
        });
    }
}

module.exports = Factory;
