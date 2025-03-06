// DEPRECATED
// ONLY IN USE FOR LEAD TRADIS STRATEGY ACCOUNT (Procyon for example)

const mongoose = require('mongoose')

const accountTransactionResults = mongoose.Schema({
    at: { type: Date, default: Date.now },
    totalUSDBeforeTrading: { type: Number },
    totalBtcBeforeTrading: { type: Number },
    AIpredictions: { type: Array },
    bought: { type: Array },
    sold: { type: Array },
}, {strict: false});

module.exports = accountTransactionResults;
