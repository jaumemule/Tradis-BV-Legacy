"use strict";
const redisClient = require('../config/redisConnection').container

const Accounts = require('../models/accounts');
const User = require('../models/user'); // do not remove, is for population
const Strategies = require('../models/strategies');
const accountName = require('../application/accountName');
const tradesResults = require('../application/tradesResults');
const accountResultsRepository = require('../infra/accountResultsRepository');
const mongoose = require('mongoose')
const encrypter = require('../config/encrypt')
, Schema = mongoose.Schema;

let self = module.exports = {

    all : function(req, res, next){
        let query = Accounts.find()

        query.exec(function (err, doc) {
            if (err) return next(err);
            if (doc == null) return res.status(404).send({ data: { code: 'data_not_found', message:'Data not found'}});
            res.send(doc);
        });
    },

    byStrategyId : function(req, res, next){
        let query = Accounts.find().where("_strategy").equals(req.params.strategyId)

        query.exec(function (err, doc) {
            if (err) return next(err);
            if (doc == null) return res.status(200).send([]);
            res.send(doc);
        });
    },

    byUserId : function(req, res, next){
        let query = Accounts.find({},'accountName _strategy _user active title')
        .populate('_strategy', 'active strategyName title description exchangeMarkets active runOnMode exchange baseCoin')
        .where("_user").equals(req.params.userId)

        query.exec(function (err, doc) {
            if (err) return next(err);
            if (doc == null) return res.status(200).send([]);
            res.send(doc);
        });
    },

    // deprecated, use state
    disable: function(req, res) {
        Accounts.findOneAndUpdate(
            { accountName: req.params.accountName }, 
            { active: false }, function (error, success) {
                if (error) {
                    res.status(400).send({message: 'error on save'})
                } else {
                    res.status(200).send({message: "disabled"})
                }
            });
    },

    mutateState: function(req, res) {

        let mutation = {}

        // add desired fields
        if (req.body.active !== undefined && typeof req.body.active === "boolean") {
            mutation['active'] = req.body.active
        }

        if (req.body.title !== undefined && typeof req.body.title === "string") {
            mutation['title'] = req.body.title
        }



        Accounts.findOneAndUpdate(
            { _id: req.params.accountId }, 
            mutation, function (error, success) {
                if (error) {
                    return res.status(400).send({message: 'error on save'})
                } else {
                    return res.status(201).send({message: "mutated"})
                }
            });
    },

    removeStrategyLink: function(req, res) {

        let mutation = {}
        mutation['_strategy'] = null

        Accounts.findOneAndUpdate(
            { _id: req.params.accountId }, 
            mutation, function (error, success) {
                if (error) {
                    return res.status(400).send({message: 'error on save'})
                } else {
                    return res.status(201).send({message: "mutated"})
                }
            });
    },

    // this is already legacy before coding, but to keep consistency
    // we will allow the user to have multiple strategies in one account, now core supports only one

    // TODO create first balance result
    swapStrategy: function(req, res, next) {

        Strategies.findOne({_id: req.body.strategyId}, function(err, strategy) {
            if (err) return next(err);
            if (strategy === null) return res.status(404).send({message: "strategy not found"})

            let query = Accounts.findOne({_id: req.params.accountId},'accountName _strategy _user active')
            .populate('_strategy', 'exchange _id')
            // .where("_user").equals(req.params.userId) // this would be cool
    
            query.exec(function (err, account) {

                if (err) return next(err);
                if (account === null) return res.status(404).send({message: "account not found"})

                if (account._strategy !== null && (account._strategy.exchange !== strategy.exchange)) {
                    return res.status(400).send({message: 'Account does not belong to the same strategy exchange'})
                } else if (account._strategy !== null && (account._strategy._id.toString() === req.body.strategyId)) {
                    return res.status(400).send({message: 'Account is already in this strategy'})
                } else {
                    Accounts.findOneAndUpdate(
                        { _id: req.params.accountId }, 
                        {_strategy: req.body.strategyId},  function (error, success) {
                            if (error) {
                                return res.status(400).send({message: 'error on save'})
                            } else {
                                tradesResults.getBalanceState(req.params.accountId, strategy._id, function(err, balanceState) {
                                    if (balanceState === null || err) return res.status(500).send({"message" : err})

                                    accountResultsRepository.insertAccountResult(balanceState, true, function(err, result) {
                                        if (err) console.log(err) // idempotent. although: TODO add monitoring and tracing
                                        return res.status(201).send({message: "mutated"})
                                    })
                                })
                            }
                        });
                }
            });
        })
    },

    create: function(req, res) {

        const AccountsModelInstance = new Accounts();

        let uniqueHash = AccountsModelInstance.generateOneDirectionHash(req.body.key + req.body.secret)

        Accounts.findOne({ uniqueHash: uniqueHash }, function(err, account) {

            if (account) {
                console.log('Account already exists for user ', req.params.userId)
                return res.status(401).send({error:'Exchange account already exists'});
            } else {
                let strategyId = req.body.strategyId

                let salt = encrypter.createSalt()
                let iv = encrypter.createIv()
    
                let key = encrypter.encrypt(req.body.key, salt, iv)
                let secret = encrypter.encrypt(req.body.secret, salt, iv)
    
                if (req.body.passphrase !== undefined && req.body.passphrase !== '') {
                    AccountsModelInstance.passphrase = encrypter.encrypt(req.body.passphrase, salt, iv)
                }
    
                AccountsModelInstance.salt = salt
                AccountsModelInstance.key = key
                AccountsModelInstance.secret = secret
                AccountsModelInstance.uniqueHash = uniqueHash
                AccountsModelInstance._strategy = strategyId ? strategyId : null
                AccountsModelInstance._user = req.params.userId
                AccountsModelInstance.owner = 'encrypted' // just for manual differentiation, ignore it
                AccountsModelInstance.accountName = accountName.generateFromUser(uniqueHash, req.params.userId)

                AccountsModelInstance.save(function(err, account) {
                    if (err) { 
                        console.log(err)
                        return res.status(500).send({error:'Could not save account'}) 
                    }

                    if (strategyId !== undefined && strategyId !== '' && strategyId !== null) {

                        tradesResults.getBalanceState(account._id, strategyId, function(err, balanceState) {
                            if (balanceState === null || err) return res.status(500).send({"message" : err})

                            accountResultsRepository.insertAccountResult(balanceState, true, function(err, result) {
                                if (err) console.log(err) // idempotent. although: TODO add monitoring and tracing
                                return res.status(201).send({message: "created"})
                            })
                        })

                    } else {
                        return res.status(201).send({message: "created"})
                    }
                })
            }
        })
    },

    // for admin panel purposes
    listWithUsers: function(req, res, next) {
        let query = Accounts.find({},'accountName _strategy _user active title')
        .populate('_user', 'email salt name surname locale termsAndConditions active accountStatus createdAt updatedAt')
        .populate('_strategy', 'exchange strategyName')

        // let secret = encrypter.decrypt(account['secret'], account['salt'])
        query.exec(function (err, doc) {
            if (err) return next(err);
            if (doc == null) return res.status(200).send([]);

            let response = JSON.parse(JSON.stringify(doc));
            response['total'] = response.length

            let bodyResponse = {}
            bodyResponse['total'] = response.length
            bodyResponse['active'] = 0
            bodyResponse['inactive'] = 0

            for (let index = 0; index < response.length; index++) {

                if(response[index]['active'] === true) {
                    bodyResponse['active'] +=1
                }

                if(response[index]['active'] === false) {
                    bodyResponse['inactive'] +=1
                }

                if(response[index]['_user']) {
                    let email = response[index]['_user']['email']
                    let salt = response[index]['_user']['salt']
                    let name = response[index]['_user']['name']
                    let surname = response[index]['_user']['surname']
                    response[index]['_user']['email'] = encrypter.decrypt(email, salt)
                    response[index]['_user']['name'] = encrypter.decrypt(name, salt)
                    response[index]['_user']['surname'] = encrypter.decrypt(surname, salt)
                    delete(response[index]['_user']['salt'])
                }

                if (index + 1 === response.length) {

                    bodyResponse['accounts'] = response
                    res.send(bodyResponse);
                }
            }
        });
    }
};
