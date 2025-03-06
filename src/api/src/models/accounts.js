var mongoose = require('mongoose')
, Schema = mongoose.Schema;

const crypto = require('crypto')

const modelSchema = mongoose.Schema({
    accountName: { type: String, unique: true },
    salt: { type: String },
    passphrase: { type: String },
    key: { type: String },
    secret: { type: String },
    uniqueHash: { type: String },
    title: { type: String, default: "No Name" }, // users can modify it
    is_lead: { type: Boolean, default: false }, // important for core processing
    _strategy : { type: Schema.Types.ObjectId, ref: 'Strategies', default: null },
    _user : { type: Schema.Types.ObjectId, ref: 'User' },
    active: { type: Boolean, default: true },
    owner: { type: String, default: 'client' }, // for pure information, no logic attached

    // feature flag after introducing restart profit. 
    // if this is not set will read from the first trade ever
    // otherwise will read from "trades" on the flagged one
    hasEverRestartedAccountProfit: { type: Boolean, default: false }, 
    createdAt: { type: Date, default: Date.now }
});

modelSchema.methods.generateOneDirectionHash = function(word) {
    return crypto
        .createHash('sha256')
        .update(word)
        .digest('hex');
};

module.exports = mongoose.model('Accounts', modelSchema);