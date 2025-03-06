"use strict";

const strategiesModel = require('../models/strategies');
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {

    lock : function(req, res, next){
        if (req.params.strategyName && req.params.mode){
            self.__performLockOrUnlock(req.params.strategyName, req.params.mode, false, true, res)
        } else {
            res.status(400).send({message: "mandatory field missing"})
        }
    },
    unlock : function(req, res, next){
        if (req.params.strategyName && req.params.mode){
            self.__performLockOrUnlock(req.params.strategyName, req.params.mode, true, true, res)
        } else {
            res.status(400).send({message: "mandatory field missing"})
        }
    },
    __performLockOrUnlock : function(strategyName, mode, activateTrading, activateStrategy, res)
    {
        strategiesModel.findOne()
        .where('strategyName')
        .equals(strategyName)
        .where('runOnMode')
        .equals(mode)
        .exec(function (err, doc){
            if (err) return next(err);                
            if (doc === null) {
                res.status(404).send({message: 'strategy does not exist'})
            } else {
                strategiesModel.findOneAndUpdate(
                    { _id: doc._id }, 
                    { activelyTrading: activateTrading, active: activateStrategy }, function (error, success) {
                        if (error) {
                            res.status(400).send({message: 'error on save, check body request'})
                        } else {
                            res.send({message: "trading lock updated"})
                        }
                });
            }  
        });
    },
    time : function(req, res, next){
        res.send({utc: new Date(new Date().toUTCString())})
    }
};
