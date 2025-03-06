const passportJwt = require('passport-jwt');
const JwtStrategy = passportJwt.Strategy;
const passportLocal = require('passport-local');
const LocalStrategy = passportLocal.Strategy;
const sqlite = require('sqlite3').verbose();
const sha1 = require('sha1');
const authConfig = require('../config/auth.js');

module.exports = function(passport) {
    let db = new sqlite.Database('./users.db', (error) => {
        error && console.log(error.message);
    });
    passport.use(
        new LocalStrategy({ passReqToCallback: false }, (username, password, done) => {
            if (db) {
                const query = 'SELECT id, username FROM users WHERE username = ? AND password = ?';
                const params = [username, sha1(password)];
                return db.get(query, params, (error, row) => {
                    if (error) {
                        return done(null, false, { message: error });
                    } else if (row) {
                        return done(null, row, { message: 'Logged in successfully' });
                    } else {
                        return done(null, false, { message: 'Invalid credentials' });
                    }
                });
            } else {
                return done(null, false, { message: 'Cannot access database' });
            }
        }),
    );

    passport.use(
        new JwtStrategy(
            {
                jwtFromRequest: passportJwt.ExtractJwt.fromAuthHeaderAsBearerToken(),
                secretOrKey: authConfig.jwtSecret,
            },
            (payload, done) => {
                return done(null, payload);
            },
        ),
    );
};
