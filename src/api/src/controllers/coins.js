"use strict";

const coinsModel = require('../models/coins');
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {

    get : function(req, res, next){
        let query = coinsModel.find().select('coin _id stopLossPercentage jumpToMarketPercentage hardLocked softLocked')

        query.exec(function (err, doc) {
            if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
            if (err) return next(err);
            res.send(doc);
        });
    },

    create : function(req, res, next){
        if (req.body.coin){

            const doc = new coinsModel(req.body);

            let query = coinsModel.find().where('coin').equals(req.body.coin).exec(function (err, doc){
                if (err) return next(err);                
                if (doc.length > 0) {
                    res.status(400).send({message: 'duplicate'})
                } else {
                    coinsModel.create(req.body, function (err, doc) {
                        if (err) return next(err);                
                        res.send({message: "created"})
                    });
                }
            })
        } else {
            res.status(400).send({message: "mandatory field missing"})
        }
    },
    update : function(req, res, next){
        coinsModel.findOneAndUpdate({_id: req.params.id }, req.body, function (err, doc) {
            if (err) {
                res.status(404).send({message: 'coin does not exist'})
            } else {
                res.send({message: "updated"})
            }               
        });
    },
    softLockForStrategy : function(req, res, next){
        if (req.body.strategy && req.body.checkedAtPrice){
            coinsModel.findOne().where('coin').equals(req.params.coinName).exec(function (err, doc){
                if (err) return next(err);                
                if (doc === null) {
                    res.status(404).send({message: 'coin does not exist'})
                } else {
                    coinsModel.findOneAndUpdate(
                        { _id: doc._id }, 
                        { $push: { softLocked: req.body } }, function (error, success) {
                            if (error) {
                                res.status(400).send({message: 'error on save, check body request'})
                            } else {
                                res.send({message: "lock created"})
                            }
                    });
                }  
            });
        } else {
            res.status(400).send({message: "mandatory field missing"})
        }
    },
    softUnlockCoinForAllStrategies : function(req, res, next){
        coinsModel.findOne().where('coin').equals(req.params.coinName).exec(function (err, doc){
            if (err) return next(err);                
            if (doc === null) {
                res.status(404).send({message: 'coin does not exist'})
            } else {
                coinsModel.findOneAndUpdate(
                { _id: doc._id }, 
                { softLocked: [] }, function (error, success) {
                    if (error) {
                        res.status(400).send({message: 'error on save, check body request'})
                    } else {
                        res.send({message: "unlocked"})
                    }
                });
            }
        });
    },
    lockedCoinsPerStrategy : function (req, res, next) {
        coinsModel.aggregate(
            [
                { "$match": {
                        "softLocked":{ $exists: true, $ne: [] },
                    },
                },
                { "$group": { 
                     _id: '$_id',
                     coin : { $first: '$coin' },
                     strategy : { $first: '$softLocked.strategy' },
                     softLocked : { $first: '$softLocked' }
                }},
                { "$project": {
                    "_id": 1,
                    "softLocked": 1,
                    "strategy": 1,
                    "coin": 1
                }}
            ]
        ).exec(function (err, doc){
            if (err) return next(err)         
            res.send(doc)
        });

    },
    desactivate : function(req, res, next){
        
    },
    activate : function(req, res, next){
        
    }
};
