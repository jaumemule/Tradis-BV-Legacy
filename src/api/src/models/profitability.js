var mongoose = require('mongoose')
, Schema = mongoose.Schema;

var Schema = mongoose.Schema({
    at: Date,
    totalBtcBeforeTrading: Number,
    totalUSDBeforeTrading: Number,
    rates: Object,
    totals: Object,
    _strategy : { type: Schema.Types.ObjectId, ref: 'Strategies', default: null },
}, {strict: false});

module.exports = Schema;
