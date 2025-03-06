const passport = require('passport');
const jwt = require('jsonwebtoken');
const authConfig = require('../config/auth.js');

module.exports = {
    login: (req, res) => {
        passport.authenticate('local', { session: false }, (error, user, info) => {
            if (error) {
                return res.status(401).json({
                    message: 'Authentication error',
                });
            } else if (user) {
                req.login(user, { session: false }, (err) => {
                    if (err) {
                        return res.send(err);
                    } else {
                        const token = jwt.sign(user, authConfig.jwtSecret);
                        return res.json({ user, token });
                    }
                });
            } else {
                return res.status(401).json({
                    message: info.message,
                });
            }
        })(req, res);
    },
};
