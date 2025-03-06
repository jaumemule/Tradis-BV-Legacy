const accountsModel = require('../models/accounts');
const strategiesModel = require('../models/strategies');
let accounts = {}
let inMemoryCcxtExchangePool = {}
const exchangeAccountCcxtConnection = require('../infra/ExchangeAccountCcxtConnection')

let self = module.exports = {
    listen: function() {
        self.__loadAccounts()    
        async function load(__loadAccounts) {
            while (true) {
                await new Promise(resolve => setTimeout(resolve, 60000)); //60 seconds refresh
                __loadAccounts()
                }
            }
            
            load(self.__loadAccounts)

        console.log('Scanning and syncing new accounts connections')
    },

    __loadAccounts: function() {

        inMemoryCcxtExchangePool = {}
        accounts = {}

        strategiesModel.find().exec(function (err, strategiesResult) {
            accountsModel.find().exec(function (err, accountsResult) {

                    accountsResult.forEach(function(account, index){
                        strategiesResult.forEach(function(strategy, index){

                            if (account['_strategy'] !== undefined && account['_strategy'] !== null) {
                                if (String(strategy['_id']) === String(account['_strategy']) 
                                && account['active'] === true
                                && account['secret'] !== undefined
                                ) {
                                    let exchange = exchangeAccountCcxtConnection.create(account, strategy)
                                    accounts[account['accountName']] = exchange
                                }
                            }
                        })
                    })

                    inMemoryCcxtExchangePool = accounts

            })
        })
    },

    connections: function(){
        return inMemoryCcxtExchangePool
    }
};

