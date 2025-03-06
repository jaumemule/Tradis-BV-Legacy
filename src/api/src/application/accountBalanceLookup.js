"use strict";

const ccxt = require('ccxt')
const accountValidation = require('./accountValidation.js');
const e = require('express');
const redisClient = require('../config/redisConnection').container

let self = module.exports = {
    retrieve: function(decryptedKey, decryptedSecret, exchange, accountName, passphrase = null, cache = true, callback) {

        let exchangeName = exchange
        if (!decryptedKey || !decryptedSecret || !exchange) {
            callback('missing fields', null)
        }

        // TODO integrate an API service
        if (!accountValidation.validExchanges().includes(exchange)) {
            callback('missing fields', null)
        }

        async function getBalances () {

            let exchangeClass = ccxt[exchangeName]

            let connection = {
                'apiKey': decryptedKey,
                'secret': decryptedSecret,
                'timeout': 30000,
                'enableRateLimit': true,
            }

            if (passphrase !== null){
                connection.password = passphrase
            }

            let exchange = new exchangeClass (connection)

            try {
                const balance = await exchange.fetchBalance()
                let expirationInSeconds = 20
                let key = 'balance_x_' + accountName
                redisClient.set(key, JSON.stringify(balance), function(err, result) {
                    redisClient.expire(key, expirationInSeconds);
                    callback(null, balance)
                })

            } catch (e) {
                console.log(e)
                callback('Invalid Exchange credentials', null)
            }
        }

        if (cache === true) {
            redisClient.get('balance_x_' + accountName, function(err, result){
                if(result === null) {
                    console.log('performing lookup for ', accountName)
                    getBalances ()
                } else {
                    console.log('from Redis',accountName)
                    callback(null, JSON.parse(result))
                }
            })
        } else {
            getBalances()
        }
    }
}