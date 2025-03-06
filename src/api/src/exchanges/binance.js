const _ = require('lodash');

class Binance {
    constructor(factory, orders, exchangeAccount, ccxtIntegration, options) {
        this.factory = factory
        this.exchangeAccount = exchangeAccount;
        this.orders = orders;
        this.ccxtIntegration = ccxtIntegration;
        this.options = options;
    };
    
    buy(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.buyFromExchange(cb, this)
    }

    sell(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.sellFromExchange(cb, this)
    }

    balances(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.balancesFromExchange(cb, this)
    }

    deposits(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.depositsFromExchange(cb, this)
    }

    withdrawals(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.withdrawalsFromExchange(cb, this)
    }

    trades(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.tradesFromExchange(cb, this)
    }

    openOrders(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.openOrdersFromExchange(cb, this)
    }

    cancelOpenOrdersForSpecificMarket(cb) {
        let ccxtIntegration = this.ccxtIntegration
        ccxtIntegration.cancelOpenOrdersForSpecificMarketFromExchange(cb, this)
    }
}

module.exports = Binance;
