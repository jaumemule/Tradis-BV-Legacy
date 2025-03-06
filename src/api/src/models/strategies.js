var mongoose = require('mongoose')

const modelSchema = mongoose.Schema({
    strategyName: { type: String, unique: true },
    active: { type: Boolean, default: false },
    activelyTrading: { type: Boolean, default: true },
    volumes: { type: Boolean, default: false },
    revertMarket: { type: Boolean, default: false },
    runOnMode: { type: String, default: 'sandbox' },
    modelFileName: { type: String, default: 'whatever.extension' },
    agentClassName: { type: String, default: 'KerasAgent' },
    exchange: { type: String, default: 'binance' },
    description: { type: String, default: '' },
    title: { type: String, default: '' },
    userAccount: { type: String, default: 'default' },
    baseCoin: { type: String, default: 'USDT' },
    runAtMinutes: { type: Array, default: [36] },
    currentCoins: { type: Array, default: [] },
    exchangeMarkets: {type: Object, default: 
        {"BTC" : {"market" : "USDT", "exchange" : "binance"},"USDT" : {"market" : "USDT", "exchange" : "binance"}}
    },
    sandboxInitialBalances: {type: Object, default: {
        "balances": {
        "BTC" : 0, // this is fleaky. always initialise per strategy, otherwise won't find the coin
        "USDT" : 100
    }}},
    trailings: {type: Object, default: {
        "BTC": {'trailingPrice' : 0}, // this is fleaky. always initialise per strategy, otherwise won't find the coin
        "USDT" : {'trailingPrice' : 0}
    }},
    trailingsPercentageConfig: {type: Object, default: {
        "stopLoss": -5,
        "jumpToMarket" : 100,
        "takeProfit" : 12
    }},
    createdAt: { type: Date, default: Date.now },
});

modelSchema.methods.fixture = function() {
    return [
        {strategyName : "keras"},
    ]
}

module.exports = mongoose.model('Strategies', modelSchema);