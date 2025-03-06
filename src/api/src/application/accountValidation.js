"use strict";

const ccxt = require('ccxt')
const validExchanges = ['binance', 'coinbasepro']

let self = module.exports = {
    validateCredentialsMiddleware: function(req, res, next) {

        if (!req.body.exchange || !req.body.key || !req.body.secret) {
            return res.status(400).send({error: 'missing fields (exchange, key, secret)'})
        }

        // TODO integrate an API service
        if (!validExchanges.includes(req.body.exchange)) {
            return res.status(400).send({error: 'invalid exchange'})
        }

        async function getBalances () {

            let exchangeId = req.body.exchange
            , exchangeClass = ccxt[exchangeId]

            let connection = {
                'apiKey': req.body.key,
                'secret': req.body.secret,
                'timeout': 30000,
                'enableRateLimit': true,
            }

            if (req.body.passphrase !== undefined && req.body.passphrase !== ''){
                connection.password = req.body.passphrase
            }

            let exchange = new exchangeClass (connection)

            try {
                await exchange.fetchBalance ()
                next()
            } catch (e) {
                console.log(e)
                return res.status(401).send({error: 'Invalid Exchange credentials'})
            }
        }

        getBalances ()
    },

    validExchanges: function() {
        return validExchanges
    }
}