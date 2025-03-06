"use strict";

const Strategies = require('../models/strategies');
const Accounts = require('../models/accounts');
const accountBalanceLookup = require('./accountBalanceLookup');
const encrypter = require('../config/encrypt')
const exchangeRatesRepository = require('../infra/exchangeRatesRepository');

// to smoke test without looking up to exchange, fake it! To add in unit tests
const fixture = {
    BTC: 100,
    USDT: 0,
    LTC: 0,
    ETH: 0,
    NEO: 0,
    CREAM: 0 
}

let self = module.exports = {
    // TODO add logging and monitoring
    getBalanceState: function(accountId, strategyId, callback)
    {
        if (accountId === null && strategyId === null) {
            return callback('Could not retrieve new exchange rate balance calculation: missing attributes')
        }

        Strategies.findOne({_id: strategyId}, function(err, strategy) {
            if (err || strategy === null) {
                return callback('Could not retrieve new exchange rate balance calculation: Strategy not found or error')
            }

            let exchangeMarkets = strategy.exchangeMarkets

            Accounts.findOne({_id: accountId}, function(err, account) {
                let userId = account._userId

                let passphrase = null
                if (account.passphrase !== undefined || account.passphrase !== '') {
                    passphrase = account.passphrase
                }

                 accountBalanceLookup.retrieve(
                    encrypter.decrypt(account.key, account.salt),
                    encrypter.decrypt(account.secret, account.salt),
                    strategy.exchange,
                    account.accountName,
                    passphrase,
                    true,
                    function(error, balance) {
                        if (error === null) {
                            // let totalBalances = fixture // to smoke test it
                            let totalBalances = balance['total']
                            let usedCoinsInStrategyList = Object.keys(exchangeMarkets);

                            let activeBalancesForStrategyDict = self.filterByUsedCoinsInStrategy(totalBalances, usedCoinsInStrategyList)
                            let coinsToComputeWithoutBaseCoinList = usedCoinsInStrategyList.filter(item => item !== strategy.baseCoin)

                            let at = new Date(Date.now() - 1000 * 1800);

                            exchangeRatesRepository.exchangeRates(strategy.baseCoin, strategy.exchange, at, null, function(err, result) {
                                if (err !== null) return callback(err, null)
                                let latestExchangeRate = result[result.length - 1] // most recent item

                                if (latestExchangeRate === null || latestExchangeRate === undefined) {
                                    return callback('latest exchange rate could not get retrieved')
                                }
                                latestExchangeRate = JSON.parse(JSON.stringify(latestExchangeRate)) // redo object (javascript things)

                                let totalInBaseCoin = 0
                                // 1. Convert all the coins in base coin (coinsToComputeWithoutBaseCoinList): loop( balance of coin * exchange rate price ), then + base coin amount
                                for (var coinInBalance in activeBalancesForStrategyDict) {
                                    if (strategy.baseCoin !== coinInBalance) { // not computing base coin, add it later (avoid crashing if not in exchange rate)

                                        // 2. Sum all the conversions to get the base coin amount
                                        let conversion = activeBalancesForStrategyDict[coinInBalance] * latestExchangeRate[coinInBalance]['p']
                                        totalInBaseCoin += conversion
                                    }
                                    
                                }
                                
                                totalInBaseCoin += activeBalancesForStrategyDict[strategy.baseCoin]

                                // 3. Now, use the result of point 2 and use exchange rate to convert to the desired coin: balance in base coin / exchange rate price
                                let totalBalanceInEveryCoinDict = {}
                                for (let i = 0; i < coinsToComputeWithoutBaseCoinList.length; i++) {
                                    let coin = coinsToComputeWithoutBaseCoinList[i]
                                    let totalInCoinFromBaseTotalAmount = totalInBaseCoin / latestExchangeRate[coin]['p']
                                    totalBalanceInEveryCoinDict[coin] = parseFloat(totalInCoinFromBaseTotalAmount.toFixed(8)) // round to 8 decimals
                                }

                                totalBalanceInEveryCoinDict[strategy.baseCoin] = totalInBaseCoin // do not forget to add base coin

                                // TODO turn it into a value object (class apart) for reusability
                                let balanceState = {
                                    exchangeRate : latestExchangeRate,
                                    activeBalancesForStrategyDict : activeBalancesForStrategyDict,
                                    totalBalanceInEveryCoinDict : totalBalanceInEveryCoinDict,
                                    baseCoin : strategy.baseCoin,
                                    userId : userId,
                                    strategyId : strategy._id,
                                    exchange: strategy.exchange,
                                    signals: strategy.currentCoins,
                                    accountId : accountId
                                }

                                return callback(null, balanceState)
                            })

                        } else {
                            return callback('error retrieving balances', balance)
                        }
                    }
                )
            })
        })
    },

    // while balances is an object {coin:amount, ...} and allowdInStrategy is array of keys ['BTC', 'USDT', ...]
    filterByUsedCoinsInStrategy: function(balances, allowedInStrategy)
    {
        return Object.keys(balances)
        .filter(key => allowedInStrategy.includes(key))
        .reduce((obj, key) => {
            return {
            ...obj,
            [key]: balances[key]
            };
        }, {});
    }
}