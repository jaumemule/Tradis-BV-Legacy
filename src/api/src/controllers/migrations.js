const coinsModel = require('../models/coinsPrices');
const mongoose = require('mongoose')

let liveCollection = mongoose.model('USDT', coinsModel, 'USDT');
let historicalCollection = mongoose.model('BTC_historical', coinsModel, 'BTC_historical');

let self = module.exports = {
    
    daily : function(req, res, next){
        var bulkInsert = historicalCollection.collection.initializeUnorderedBulkOp()
        var bulkRemove = liveCollection.collection.initializeUnorderedBulkOp()
        var date = new Date()
        date.setDate(date.getDate() -1)
        var x = 2000
        var counter = 0

        liveCollection.count({"date":{$lt: date}}, function(err, totalDocuments) {

            if(totalDocuments === 0){
                res.send("NO DAILY DATA FOR MIGRATION");   
            }
            
            liveCollection.collection.find({"date":{$lt: date}}).forEach(
                function(doc){
                    bulkInsert.insert(doc);
                    bulkRemove.find({_id:doc._id}).removeOne();
                    counter ++
                    if( counter % x == 0){      
                        bulkInsert.execute()
                        bulkRemove.execute()
                        bulkInsert = historicalCollection.collection.initializeUnorderedBulkOp()
                        bulkRemove = liveCollection.collection.initializeUnorderedBulkOp()
                    }

                    if(totalDocuments === counter){
                        //INSERT LAST ONES BELOW 2000
                        bulkInsert.execute()
                        bulkRemove.execute()
                        bulkInsert = historicalCollection.collection.initializeUnorderedBulkOp()
                        bulkRemove = liveCollection.collection.initializeUnorderedBulkOp()
                        res.send("DAILY DATA MIGRATED");                    
                    }
                }
            )
        });
    },
    removeSeveralDaysOfMainCollection : function(req, res, next){
        var date = new Date()
        date.setDate(date.getDate() -14) // KEEP 14 days of data
        liveCollection.collection.remove({"date":{$lt: date}}, function(err) {
            if (!err) res.send('OK')
            else res.send('BAD', 400)                    
        });
    }
}
