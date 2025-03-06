const ccxt = require('ccxt')
const encrypter = require('../config/encrypt')

let self = module.exports = {
    create: function (account, strategy) {
        if (String(strategy['_id']) === String(account['_strategy']) 
        && account['active'] === true
        && account['secret'] !== undefined
        ) {
            
            let exchangeId = strategy['exchange']
            , exchangeClass = ccxt[exchangeId]

            let key = encrypter.decrypt(account['key'], account['salt'])
            let secret = encrypter.decrypt(account['secret'], account['salt'])
            
            let connection = {
                'apiKey': key,
                'secret': secret,
                'timeout': 30000,
                'enableRateLimit': true,
            }

            if (account['passphrase'] !== undefined && account['passphrase'] !== ''){
                connection.password = encrypter.decrypt(account['passphrase'], account['salt'])
            }

            return new exchangeClass (connection)
        }
    }
}