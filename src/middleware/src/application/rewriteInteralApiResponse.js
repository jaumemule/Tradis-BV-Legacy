const errorHandler = require('../config/errorHandling.js');

let self = (module.exports = {
    currentExchangeRates: function(req, res, next) {
        // return only one index
        let index = res.proxyBody.length - 1;
        res.proxyBody = res.proxyBody[index];
        next();
    },
    accountBalance: function(req, res, next) {
        // return only one index
        if (res.proxyBody[req.params.accountName]['result']['error'] !== undefined) {
            res.proxyBody = errorHandler.taggedError(errorHandler.account_not_active);
            res.proxyHttpResponse.statusCode = 404;
        } else {
            res.proxyBody = res.proxyBody[req.params.accountName]['result']['total'];
        }

        next();
    },

    accountBalanceStoreInMemory: function(req, res, next) {
        if (res.proxyHttpResponse.statusCode !== 200) {
            return res
                .status(res.proxyHttpResponse.statusCode)
                .send({ error: 'could not calculate profit balance state' });
        } else {
            res.balanceStateProxyResponse = res.proxyBody;
            next();
        }
    },

    userAccountsFirstBalanceStoreInMemory: function(req, res, next) {
        if (res.proxyHttpResponse.statusCode !== 200)
            return res
                .status(res.proxyHttpResponse.statusCode)
                .send({ error: 'could not calculate profit on first balance lookup' });
        res.firstBalanceProxyResponse = res.proxyBody;
        next();
    },

    userAccountBalanceStoreInMemory: function(req, res, next) {
        if (res.proxyHttpResponse.statusCode !== 200)
            return res
                .status(res.proxyHttpResponse.statusCode)
                .send({ error: 'could not calculate profit on balance lookup' });
        if (res.proxyBody.error !== undefined)
            return res.status(404).send({ error: 'first balance is empty' });
        res.balanceProxyResponse = res.proxyBody;
        next();
    },

    currentExchangeRatesStoreInMemory: function(req, res, next) {
        if (res.proxyHttpResponse.statusCode !== 200)
            return res
                .status(res.proxyHttpResponse.statusCode)
                .send({ message: 'could not calculate profit on retrieving exchange rates' });

        if (!res.proxyBody) return res.status(404).send({ message: 'exchange rates are empty' });

        if (!'BTC' in res.proxyBody) {
            console.log('exchangeRates error: ', res.proxyBody);
            return res.status(404).send({
                message: 'Could not fetch exchange rates. Plase, come back soon or contact us',
            });
        }

        if (!'p' in res.proxyBody['BTC']) {
            console.log('exchangeRates error: ', res.proxyBody);
            return res.status(404).send({
                message:
                    'Could not fetch exchange rates indicators. Plase, come back soon or contact us',
            });
        }

        res.exchangeRatesProxyResponse = res.proxyBody;
        next();
    },
    strategies: function(req, res, next) {
        let body = res.proxyBody;
        let mappedResponse = [];

        body.forEach((strategy) => {
            if (strategy.active === true) {
                let map = {};

                // map items here to be exposed publicly
                map.baseCoin = strategy.baseCoin;

                let tradingPairs = [];

                for (coin in strategy.exchangeMarkets) {
                    if (coin !== strategy['baseCoin']) {
                        let pair = coin + '/' + strategy['baseCoin'];
                        tradingPairs.push(pair);
                    }
                }

                map.coinPairs = tradingPairs;
                map.title = strategy.title;
                map.id = strategy._id;
                map.exchange = strategy.exchange;
                map.description = strategy.description;
                mappedResponse.push(map);
            }
        });

        res.proxyBody = mappedResponse;
        next();
    },
    userAccounts: function(req, res, next) {
        // we map strategies since the body must cointain certain public attributes
        let wallets = res.proxyBody;

        wallets.forEach((account) => {
            let map = {};
            if (account._strategy !== null) {
                console.log(account._strategy);
                let strategy = account._strategy;

                // map items here to be exposed publicly
                map.baseCoin = strategy.baseCoin;

                let tradingPairs = [];

                for (coin in strategy.exchangeMarkets) {
                    if (coin !== strategy['baseCoin']) {
                        let pair = coin + '/' + strategy['baseCoin'];
                        tradingPairs.push(pair);
                    }
                }

                map.coinPairs = tradingPairs;
                map.title = strategy.title;
                map.exchange = strategy.exchange;
                map.description = strategy.description;
                map.active = strategy.active;
                map._id = strategy._id;

                // deprecation
                map.strategyName = strategy.strategyName;
                map.runOnMode = strategy.runOnMode;

                account._strategy = map;
            }
        });

        next();
    },
});

/*
[ { active: false,
    activelyTrading: true,
    volumes: false,
    revertMarket: false,
    runOnMode: 'simulation',
    modelFileName: 'BTC_2018-2019-weights.h5f',
    agentClassName: 'KerasAgent',
    exchange: 'binance',
    userAccount: 'default',
    baseCoin: 'USDT',
    runAtMinutes: [ 50 ],
    currentCoins: [],
    exchangeMarkets: { BTC: [Object], USDT: [Object] },
    sandboxInitialBalances: { balances: [Object] },
    trailings: { BTC: [Object], USDT: [Object] },
    trailingsPercentageConfig: { stopLoss: -0.5, jumpToMarket: 100, takeProfit: 100 }
    */
