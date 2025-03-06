const ActionAttempts = require('../models/actionAttempts.js');
const errorHandler = require('../config/errorHandling.js');

const fixedMinutesToFreezeActions = 120;
const maxNumberOfLoginAttempts = 7;
const maxNumberOfAccountRegistrations = 2;

let self = (module.exports = {
    isUserReachingTheLimitOfLoginAttempts: function(req, res, next) {
        let now = new Date(new Date().toUTCString());
        let untilDate = new Date(new Date().toUTCString());
        untilDate.setTime(now.getTime() - fixedMinutesToFreezeActions * 60 * 1000);
        let ip =
            req.headers['x-forwarded-for'] ||
            req.connection.remoteAddress ||
            req.socket.remoteAddress ||
            (req.connection.socket ? req.connection.socket.remoteAddress : null);
        let userAgent = req.get('user-agent');

        ActionAttempts.findOne({ ip: ip, userAgent: userAgent })
            .where({ date: { $gt: untilDate } })
            .and({ action: 'login' })
            .exec(function(err, db_res) {
                if (!db_res) {
                    next();
                } else {
                    if (db_res.NumberOfAttempts >= maxNumberOfLoginAttempts) {
                        res.status(401).send(
                            errorHandler.taggedError(errorHandler.max_number_of_login_attempts),
                        );
                    } else {
                        next();
                    }
                }
            });
    },
    isUserReachingTheLimitOfRegistrationAttempts: function(req, res, next) {
        let now = new Date(new Date().toUTCString());
        let untilDate = new Date(new Date().toUTCString());
        untilDate.setTime(now.getTime() - fixedMinutesToFreezeActions * 60 * 1000);
        let ip =
            req.headers['x-forwarded-for'] ||
            req.connection.remoteAddress ||
            req.socket.remoteAddress ||
            (req.connection.socket ? req.connection.socket.remoteAddress : null);
        let userAgent = req.get('user-agent');

        ActionAttempts.findOne({ ip: ip, userAgent: userAgent })
            .where({ date: { $gt: untilDate } })
            .and({ action: 'register' })
            .exec(function(err, db_res) {
                if (!db_res) {
                    next();
                } else {
                    if (db_res.NumberOfAttempts >= maxNumberOfAccountRegistrations) {
                        res.status(401).send(
                            errorHandler.taggedError(
                                errorHandler.max_number_of_registration_attempts,
                            ),
                        );
                    } else {
                        next();
                    }
                }
            });
    },
    registerAttemptWithAction(ip, userAgent, action, cb) {
        let now = new Date(new Date().toUTCString());
        let untilDate = new Date(new Date().toUTCString());
        untilDate.setTime(now.getTime() - fixedMinutesToFreezeActions * 60 * 1000);

        ActionAttempts.findOneAndUpdate(
            { ip: ip, userAgent: userAgent },
            { $inc: { NumberOfAttempts: 1 } },
        )
            .select('date NumberOfAttempts')
            .where({ date: { $gt: untilDate } })
            .and({ action: action })
            .exec(function(err, db_res) {
                if (err) {
                    console.log(err);
                    cb();
                } else {
                    if (!db_res) {
                        actionAttempts = new ActionAttempts();
                        actionAttempts.ip = ip;
                        actionAttempts.userAgent = userAgent;
                        actionAttempts.NumberOfAttempts = 1;
                        actionAttempts.action = action;
                        actionAttempts.date = now;

                        actionAttempts.save(function(error, response) {
                            if (!error) {
                                cb();
                            } else {
                                console.log(error);
                                cb();
                            }
                        });
                    } else {
                        cb();
                    }
                }
            });
    },
});
