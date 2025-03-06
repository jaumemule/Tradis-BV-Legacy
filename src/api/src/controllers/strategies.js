"use strict";

const strategiesModel = require('../models/strategies');
const mongoose = require('mongoose')
, Schema = mongoose.Schema;

let self = module.exports = {

    get : function(req, res, next){
        let query = strategiesModel.find()

        query.exec(function (err, doc) {
            if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
            if (err) return next(err);
            res.send(doc);
        });
    },

    getById : function(req, res, next){
        let query = strategiesModel.findOne().where('strategyName').equals(req.params.strategyName)

        query.exec(function (err, doc) {
            if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
            if (err) return next(err);
            res.send(doc);
        });
    },

    create : function(req, res, next){
        if (req.body.strategyName){

            const doc = new strategiesModel(req.body);

            let query = strategiesModel.find().where('strategyName').equals(req.body.strategyName).exec(function (err, doc){
                if (err) return next(err);                
                if (doc.length > 0) {
                    res.status(400).send({message: 'duplicate'})
                } else {
                    strategiesModel.create(req.body, function (err, doc) {
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
        
        const doc = new strategiesModel(req.body);

        let query = strategiesModel.findOne().where('strategyName').equals(req.params.strategyName).exec(function (err, docResult){
            if (err) return next(err);
            if (docResult === null) {
                res.status(404).send({message: 'strategy does not exist'})
            } else {
                strategiesModel.findOneAndUpdate({_id: docResult._id }, req.body, function (err, doc) {
                    if (err) {
                        res.status(400).send({message: 'error happened'})
                    } else {
                        res.send({message: "updated"})
                    }               
                });
            }
        })
    },
    // TODO this makes sense depending on the role of the user, we can set a middleware
    lock : function(req, res, next){
        
    },
    unlock : function(req, res, next){
        
    },
    desactivate : function(req, res, next){
        
    },
    activate : function(req, res, next){
        
    }
};
