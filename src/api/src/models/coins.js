var mongoose = require('mongoose')

const modelSchema = mongoose.Schema({
    coin: { type: String, unique: true },
    active: { type: Boolean, default: true },
    softLocked: [{ 
        strategy: String,
        checkedAtPrice: Number,
        stoppedAtLossPercentage: Number,
        createdAt: { type: Date, default: Date.now }
     }],    
    hardLocked: { type: Boolean, default: false },
    stopLossPercentage: { type: Number, default: 1 },
    createdAt: { type: Date, default: Date.now }
});

modelSchema.methods.fixture = function() {
    return [
{coin: "EUR"},
{coin: "USDT"},
{coin: "BTC"},
    ]
}

module.exports = mongoose.model('Coins', modelSchema);
