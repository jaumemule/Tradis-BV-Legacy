const errorHandler = require('../config/errorHandling.js');
const User = require('../models/user.js');
const UserToken = require('../application/userToken');
const loginAttemptsMiddleware = require('../application/loginAttemptsMiddleware');
const encrypter = require('../config/encrypt');

const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const MaxUsersSchema = new Schema({ max: Number }, { strict: false });
const MaxUsers = mongoose.model('MaxUsers', MaxUsersSchema, 'max_users');

var SibApiV3Sdk = require('sib-api-v3-sdk');
var defaultClient = SibApiV3Sdk.ApiClient.instance;
var apiKey = defaultClient.authentications['api-key'];
apiKey.apiKey = process.env.SENDIN_BLUE_API_KEY;

module.exports = {
    updateScreenState: (req, res) => {
        if (typeof req.body.screenState !== 'string') {
            return res.status(400).send();
        }

        User.updateOne(
            { _id: req.body.userSession.uid },
            { screenState: req.body.screenState },
            function(err, user) {
                if (err)
                    return res
                        .status(500)
                        .send(errorHandler.taggedError(errorHandler.system_error));
                if (user) return res.status(201).send({});
            },
        );
    },
    getScreenState: (req, res) => {
        User.findOne({ _id: req.body.userSession.uid }, function(err, user) {
            if (err)
                return res.status(500).send(errorHandler.taggedError(errorHandler.system_error));
            if (user) {
                let response = { screenState: user['screenState'] ? user['screenState'] : null };
                return res.status(201).send(response);
            }
        });
    },
    register: (req, res, next) => {
        if (
            !req.body ||
            !req.body.email ||
            !req.body.password ||
            !req.body.name ||
            !req.body.surname
        )
            return res.status(400).send(errorHandler.taggedError(errorHandler.missing_fields));

        let password = req.body.password;
        let email = req.body.email;
        let name = req.body.name;
        let surname = req.body.surname;

        let regexPasswordValidation = new RegExp('^(?=.{8,})');

        let ip =
            req.headers['x-forwarded-for'] ||
            req.connection.remoteAddress ||
            req.socket.remoteAddress ||
            (req.connection.socket ? req.connection.socket.remoteAddress : null);

        let userAgent = req.get('user-agent');

        if (!/[a-z]/.test(name)) {
            return res.status(400).send(errorHandler.taggedError(errorHandler.missing_fields));
        }

        if (!/[a-z]/.test(surname)) {
            return res.status(400).send(errorHandler.taggedError(errorHandler.missing_fields));
        }

        if (!regexPasswordValidation.test(password)) {
            return res
                .status(400)
                .send(errorHandler.taggedError(errorHandler.invalid_password_registration));
        }

        if (
            !/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(
                email,
            )
        ) {
            return res
                .status(400)
                .send(errorHandler.taggedError(errorHandler.email_format_not_valid));
        }

        UserModel = new User();
        let hashedEmail = UserModel.generateOneDirectionHash(email);

        User.findOne({ emailHash: hashedEmail }, function(err, user) {
            if (err)
                return res.status(500).send(errorHandler.taggedError(errorHandler.system_error));

            if (user) {
                return res
                    .status(401)
                    .send(errorHandler.taggedError(errorHandler.email_already_registered));
            } else {
                let NewUser = new User();

                let hash = NewUser.generateRandomHash();
                let salt = encrypter.createSalt();
                let iv1 = encrypter.createIv();
                let emailHash = NewUser.generateOneDirectionHash(email);

                NewUser.email = encrypter.encrypt(email, salt, iv1);
                NewUser.emailHash = emailHash;
                NewUser.name = encrypter.encrypt(name, salt, iv1);
                NewUser.salt = salt;
                NewUser.surname = encrypter.encrypt(surname, salt, iv1);
                NewUser.accountStatus = 'pending';
                NewUser.active = false;

                // TODO remove this once we have the portal
                if (req.query.verified == true) {
                    NewUser.accountStatus = 'active';
                    NewUser.active = true;
                }

                NewUser.password = NewUser.generateHash(password);
                NewUser.changePassword.hash = hash;
                NewUser.changePassword.used = false;
                NewUser.changePassword.expires = NewUser.hashRenewPasswordExpirationTime(10080); // 1 week

                NewUser.save(function(err, doc) {
                    if (err)
                        return res
                            .status(500)
                            .send(
                                errorHandler.taggedError(
                                    errorHandler.system_error,
                                    'Could not save user',
                                ),
                            );

                    var apiInstance = new SibApiV3Sdk.SMTPApi();

                    var sendSmtpEmail = new SibApiV3Sdk.SendSmtpEmail(); // SendSmtpEmail | Values to send a transactional email

                    let callbackUrl = '';
                    let uri = '/email_verified/?id=' + doc._id + '&hash=' + hash;
                    // for development
                    if (req.query.forceLocalhostCallback === '1') {
                        callbackUrl = 'http://localhost:8000' + uri;
                    } else {
                        let baseUrl = process.env.BASE_URL || 'http://localhost:8000';
                        callbackUrl = baseUrl + uri;
                    }

                    sendSmtpEmail.templateId = 10;
                    sendSmtpEmail.to = [{ email: email, name: name }];
                    sendSmtpEmail.sender = { email: 'info@tradis.ai', name: 'Tradis' };
                    sendSmtpEmail.subject = 'Verify your account';
                    sendSmtpEmail.headers = { 'x-mailin-custom': 'myV3Custom' };
                    sendSmtpEmail.params = { name: name, verification_url: callbackUrl };
                    sendSmtpEmail.textContent = 'Verify your account!';

                    if (doc.active === false) {
                        apiInstance.sendTransacEmail(sendSmtpEmail).then(
                            function(data) {
                                console.log(
                                    'Sendinblue API called successfully. Returned data: ' + data,
                                );

                                return loginAttemptsMiddleware.registerAttemptWithAction(
                                    ip,
                                    userAgent,
                                    'register',
                                    function() {
                                        return res.status(201).send({});
                                    },
                                );
                            },
                            function(error) {
                                console.error(error);
                                return loginAttemptsMiddleware.registerAttemptWithAction(
                                    ip,
                                    userAgent,
                                    'register',
                                    function() {
                                        return res
                                            .status(500)
                                            .send(
                                                errorHandler.taggedError(
                                                    errorHandler.system_error,
                                                    'Could not send email for registration (check logs)',
                                                ),
                                            );
                                    },
                                );
                            },
                        );
                    } else {
                        return res.status(201).send({});
                    }
                });
            }
        });
    },

    registerConfirm: (req, res) => {
        User.findOne({ _id: req.params.userId }, function(err, user) {
            let currentTimestamp = new Date().getTime();

            if (err)
                return res.status(500).send(errorHandler.taggedError(errorHandler.system_error));
            if (!user)
                return res.status(404).send(errorHandler.taggedError(errorHandler.token_expired)); // do not tell user exists or not
            if (user.changePassword.hash != req.params.hash)
                return res.status(401).send(errorHandler.taggedError(errorHandler.token_expired));
            if (currentTimestamp > user.changePassword.expires)
                return res.status(403).send(errorHandler.taggedError(errorHandler.token_expired));

            let payload = {
                active: true,
                accountStatus: 'active',
                changePassword: {},
            };

            User.updateOne({ _id: user._id }, payload, function(err, user) {
                if (err)
                    return res
                        .status(500)
                        .send(errorHandler.taggedError(errorHandler.system_error));
                if (user) return res.status(201).send({});
            });
        });
    },

    changePasswordGenerate: (req, res) => {
        if (!req.body.email)
            return res.send(400, errorHandler.taggedError(errorHandler.missing_fields));

        if (
            !/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(
                req.body.email,
            )
        ) {
            return res
                .status(400)
                .send(errorHandler.taggedError(errorHandler.email_format_not_valid));
        }

        UserModel = new User();
        let hashedEmail = UserModel.generateOneDirectionHash(req.body.email);

        User.findOne({ emailHash: hashedEmail }, function(err, user) {
            if (!user)
                // NOTE: this is idempotent. we do not tell attackers if user exists
                return res.status(201).send({});

            let UserSchema = new User();

            let hashString = UserSchema.generateRandomHash();

            let query = User.updateOne(
                { _id: user._id },
                {
                    changePassword: {
                        hash: hashString,
                        used: false,
                        expires: UserSchema.hashRenewPasswordExpirationTime(20),
                    },
                },
            );

            var apiInstance = new SibApiV3Sdk.SMTPApi();

            var sendSmtpEmail = new SibApiV3Sdk.SendSmtpEmail(); // SendSmtpEmail | Values to send a transactional email

            let unencryptedUserEmail = encrypter.decrypt(user.email, user.salt);
            let unencryptedUserName = encrypter.decrypt(user.name, user.salt);

            let callbackUrl = '';
            let uri = '/password_changed/?id=' + user._id + '&hash=' + hashString;

            // for development
            if (req.query.forceLocalhostCallback === '1') {
                callbackUrl = 'http://localhost:8000' + uri;
            } else {
                let baseUrl = process.env.BASE_URL || 'http://localhost:8000';
                callbackUrl = baseUrl + uri;
            }

            sendSmtpEmail.templateId = 11;
            sendSmtpEmail.to = [{ email: unencryptedUserEmail, name: unencryptedUserName }];
            sendSmtpEmail.sender = { email: 'info@tradis.ai', name: 'Tradis' };
            sendSmtpEmail.subject = 'Reset your password';
            sendSmtpEmail.headers = { 'x-mailin-custom': 'myV3Custom' };
            sendSmtpEmail.params = { reset_url: callbackUrl };
            sendSmtpEmail.textContent = 'Reset your password';

            apiInstance.sendTransacEmail(sendSmtpEmail).then(
                function(data) {
                    console.log('Sendinblue API called successfully. Returned data: ' + data);

                    query.exec(function(err) {
                        if (err) return next(err);
                        return res.status(201).send({});
                    });
                },
                function(error) {
                    console.error(error);
                    return res
                        .status(500)
                        .send(
                            errorHandler.taggedError(
                                errorHandler.system_error,
                                'Could not send email for password reset (chech logs)',
                            ),
                        );
                },
            );
        });
    },

    changePasswordConfirm: (req, res) => {
        User.findOne({ _id: req.params.userId }, function(err, user) {
            let currentTimestamp = new Date().getTime();

            if (!req.body || !req.body.password)
                return res.status(400).send(errorHandler.taggedError(errorHandler.missing_fields));

            let password = req.body.password;

            let regexPasswordValidation = new RegExp('^(?=.{8,})');

            if (!regexPasswordValidation.test(password)) {
                return res
                    .status(400)
                    .send(errorHandler.taggedError(errorHandler.invalid_password_registration));
            }

            if (err)
                return res.status(500).send(errorHandler.taggedError(errorHandler.system_error));
            if (!user)
                return res.status(401).send(errorHandler.taggedError(errorHandler.token_expired)); // do not show user not found!
            if (user.changePassword.hash != req.params.hash)
                return res.status(401).send(errorHandler.taggedError(errorHandler.token_expired));
            if (currentTimestamp > user.changePassword.expires)
                return res.status(403).send(errorHandler.taggedError(errorHandler.token_expired));

            let UserSchema = new User();

            let payload = {
                changePassword: {},
                password: UserSchema.generateHash(password),
            };

            User.updateOne({ _id: user._id }, payload, function(err) {
                if (err)
                    return res
                        .status(500)
                        .send(errorHandler.taggedError(errorHandler.system_error));
                return res.status(201).send({});
            });
        });
    },

    login: (req, res, next) => {
        if (!req.body || !req.body.password || !req.body.email)
            return res.status(400).send(errorHandler.taggedError(errorHandler.missing_fields));

        let password = req.body.password;
        let email = req.body.email;

        if (
            !/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(
                email,
            )
        ) {
            return res
                .status(400)
                .send(errorHandler.taggedError(errorHandler.email_format_not_valid));
        }

        UserModel = new User();

        let ip =
            req.headers['x-forwarded-for'] ||
            req.connection.remoteAddress ||
            req.socket.remoteAddress ||
            (req.connection.socket ? req.connection.socket.remoteAddress : null);

        let userAgent = req.get('user-agent');

        let hashedEmail = UserModel.generateOneDirectionHash(req.body.email);

        User.findOne({ emailHash: hashedEmail }, function(err, user) {
            if (!user) {
                return loginAttemptsMiddleware.registerAttemptWithAction(
                    ip,
                    userAgent,
                    'login',
                    function() {
                        res.status(404).send(
                            errorHandler.taggedError(errorHandler.invalid_password_or_email),
                        );
                    },
                );
            }
            if (user.accountStatus != 'active') {
                return loginAttemptsMiddleware.registerAttemptWithAction(
                    ip,
                    userAgent,
                    'login',
                    function() {
                        res.status(401).send(
                            errorHandler.taggedError(errorHandler.account_not_active),
                        );
                    },
                );
            }

            let userSchema = new User();

            if (!userSchema.validPassword(password, user.password)) {
                return loginAttemptsMiddleware.registerAttemptWithAction(
                    ip,
                    userAgent,
                    'login',
                    function() {
                        res.status(404).send(
                            errorHandler.taggedError(errorHandler.invalid_credentials),
                        );
                    },
                );
            }

            let hash = userSchema.generateRandomHash();
            let unencryptedToken = userSchema.createSessionToken(user._id, hash);

            UserToken.createToken(unencryptedToken, function(tokenObject) {
                if (!tokenObject)
                    return res
                        .status(500)
                        .send(
                            errorHandler.taggedError(
                                errorHandler.system_error,
                                'Could not generate token',
                            ),
                        );

                let sessionsTokens = user.availableSessionsHash ? user.availableSessionsHash : [];

                sessionsTokens.push(hash);

                let payload = {
                    availableSessionsHash: sessionsTokens,
                };

                User.updateOne({ _id: user._id }, payload, function(err) {
                    if (err)
                        return res
                            .status(500)
                            .send(errorHandler.taggedError(errorHandler.system_error));

                    return res.status(201).send({
                        data: {
                            token: tokenObject.access_token,
                            email: email,
                            expires: tokenObject.expires_in,
                        },
                    });
                });
            });
        });
    },

    logout: (req, res) => {
        let payload = {
            availableSessionsHash: [],
        };

        User.updateOne({ _id: req.body.userSession.uid }, payload, function(err) {
            if (err)
                return res.status(500).send(errorHandler.taggedError(errorHandler.system_error));

            if (!err) return res.status(204).send();
        });
    },

    // this is to control growth
    isMaxUsersAchieved: (req, res) => {
        User.estimatedDocumentCount({}, function(err, totalActiveUsers) {
            MaxUsers.find({}, function(err, maxUsersDoc) {
                if (totalActiveUsers >= maxUsersDoc[0].max) {
                    res.status(401).send({ max_users_reached: true });
                } else {
                    res.status(200).send({ max_users_reached: false });
                }
            });
        });
    },
};
