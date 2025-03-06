'use strict';

const jwt = require('jsonwebtoken');
const User = require('../models/user.js');
const errorHandler = require('../config/errorHandling.js');

let self = (module.exports = {
    signature: '54#$%sd659asdAA7878&&!.A0)(?%2@34%5FhsSgIOdfkg?_~vmerASL:Dsfgdjflk%5675rthgf',

    createToken: function(uid, cb) {
        let token = jwt.sign(
            {
                uid: uid,
            },
            self.signature,
            { expiresIn: '1y' },
        );

        let tokenInfo = {};

        jwt.verify(token, self.signature, function(err, decoded) {
            if (err) return false;

            tokenInfo.access_token = token;
            tokenInfo.expires_in = decoded.exp;
            cb(tokenInfo);
        });
    },
    verifyTokenAndSetDecryptedUserToRequestObject: function(req, res, next) {
        if (req.headers.authorization == undefined)
            return res.status(401).send(errorHandler.taggedError(errorHandler.token_app_not_valid));

        jwt.verify(req.headers.authorization, self.signature, function(err, decoded) {
            if (err)
                return res
                    .status(500)
                    .send(
                        errorHandler.taggedError(
                            errorHandler.system_error,
                            'Could not decode token',
                        ),
                    );

            let userId = decoded.uid.split(':')[0];
            let session = decoded.uid.split(':')[1];

            req.body.userSession = {};
            req.body.userSession.uid = userId;
            req.body.userSession.iat = decoded.iat;
            req.body.userSession.exp = decoded.exp;
            req.body.userSession.session = session;
            req.body.userSession.role = undefined; // to check later

            User.findOne({ _id: userId }, function(err, user) {
                if (!user)
                    return res
                        .status(404)
                        .send(errorHandler.taggedError(errorHandler.user_not_found));

                if (user.accountStatus != 'active')
                    return res
                        .status(401)
                        .send(errorHandler.taggedError(errorHandler.account_not_active));

                let sessionsTokens = user.availableSessionsHash ? user.availableSessionsHash : [];

                if (user.role !== undefined) {
                    req.body.userSession.role = user.role;
                }

                if (!sessionsTokens.includes(session)) {
                    return res
                        .status(404)
                        .send(errorHandler.taggedError(errorHandler.token_app_not_valid));
                }

                next();
            });
        });
    },
    verifyAdminRootRole: function(req, res, next) {
        if (req.body.userSession.role === undefined) {
            return res.status(401).send('No permissions to perform this action');
        } else if (req.body.userSession.role !== 'admin_root') {
            return res.status(401).send('Not enough permissions to perform this action');
        } else {
            next();
        }
    },
});
