var mongoose = require('mongoose')
, Schema = mongoose.Schema;

var coinsSchema = mongoose.Schema({
    date: Date
}, {strict: false});

module.exports = coinsSchema;
