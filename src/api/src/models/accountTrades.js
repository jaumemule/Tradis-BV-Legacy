const mongoose = require('mongoose')
, Schema = mongoose.Schema;

const modelSchema = mongoose.Schema({
    at: { type: Date, default: Date.now },
    _account : { type: Schema.Types.ObjectId, ref: 'Accounts' },
    _user : { type: Schema.Types.ObjectId, ref: 'User' },
    totalUSDBeforeTrading: { type: Number }, // deprecated, use totals
    totalBtcBeforeTrading: { type: Number }, // deprecated, use totals
    exchange: { type: String },
    baseCoin: { type: String },
    BTCvalue: { type: Number }, // deprecated, use rates
    USDvalue: { type: Number }, // deprecated, use rates
    AIpredictions: { type: Array }, // deprecaed, use signals
    rates: { type: Object },
    balances: { type: Object },
    totals: { type: Object }, // total balance with coin conversion already computed
    bought: { type: Array },
    sold: { type: Array },
    signals: { type: Array },
    _strategy : { type: Schema.Types.ObjectId, ref: 'Strategies' },
    resultCalculationStartingPoint: { type: Boolean, default: false },
}, {strict: false});

module.exports = mongoose.model('trades', modelSchema);