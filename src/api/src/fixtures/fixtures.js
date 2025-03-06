"use strict"
var coinsModel = require('../models/coins.js');
var strategiesModel = require('../models/strategies.js');

let self = module.exports = {
    coinsListWithPercentages : function(success, alreadyPopulated){

        coinsModel.count(function (err, count) {
            if (!err && count === 0) {
                let coinsModelInstance = new coinsModel
                let fixtureCoins = coinsModelInstance.fixture()

                let counter = 1

                fixtureCoins.forEach(function(coin) {

                    coinsModel.create(coin, function (err, doc) {

                        if (counter === fixtureCoins.length) {
                            success()                 
                        }

                        counter++
                        
                    });
                }, this);
            } else {
                alreadyPopulated()
            }
        });
    },
    strategies : function(success, alreadyPopulated){

        strategiesModel.count(function (err, count) {
            if (!err && count === 0) {
                let strategiesModelInstance = new strategiesModel
                let fixtureCoins = strategiesModelInstance.fixture()

                let counter = 1

                fixtureCoins.forEach(function(coin) {

                    strategiesModel.create(coin, function (err, doc) {

                        if (counter === fixtureCoins.length) {
                            success()                 
                        }

                        counter++
                        
                    });
                }, this);
            } else {
                alreadyPopulated()
            }
        });
    }
}
