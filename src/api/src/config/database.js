module.exports = {
    'url' : process.env.MONGO_CONNECTION || 'mongodb://localhost:27017/aggregated',
    nomenclaturePerStrategy : function(strategy){
        return strategy['strategyName'] + '_' + strategy['baseCoin'] + '_' + strategy['runOnMode'] 
    }
};