const mongoose = require('mongoose');

var schema = mongoose.Schema({
    action: String,
    ip: String,
    userAgent: String,
    NumberOfAttempts: Number,
    date: { type: Date, default: Date.now },
});

module.exports = mongoose.model('ActionAttempts', schema);
