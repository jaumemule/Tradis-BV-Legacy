"use strict";
const redisClient = require('../config/redisConnection').container

const Accounts = require('../models/accounts');
const Users = require('../models/user');
const mongoose = require('mongoose')
const Strategies = require('../models/strategies'); // used for population
const encrypter = require('../config/encrypt')
, Schema = mongoose.Schema;

let self = module.exports = {
    // for admin panel purposes
    listWithWallets: function(req, res, next) {
        let counter = 0

        Users.find({},'_id email name surname salt locale active accountStatus createdAt')
        .lean()
        .exec(function(err, users) {

            let response = JSON.parse(JSON.stringify(users));

            for (let index = 0; index < response.length; index++) {

                let email = response[index]['email']
                let salt = response[index]['salt']
                let name = response[index]['name']
                let surname = response[index]['surname']
                response[index]['email'] = encrypter.decrypt(email, salt)
                response[index]['name'] = encrypter.decrypt(name, salt)
                response[index]['surname'] = encrypter.decrypt(surname, salt)
                delete(response[index]['salt'])

                function getWallets(response, cb) {
                    Accounts.find({}, 'title is_lead active accountName _id hasEverRestartedAccountProfit').where({'_user' : response[index]['_id']})
                    .populate('_strategy', 'exchange strategyName title description')
                    .exec(function(err, wallet) {
                        response[index]['wallets'] = wallet
                        cb(response)
                    })
                }

                getWallets(response, function(nextResponse){
                    counter++
                    if (counter + 1 === response.length) {
                        res.send(nextResponse);
                    }
                })
            }
        })
    }
}