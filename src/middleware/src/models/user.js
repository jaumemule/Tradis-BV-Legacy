// app/models/user.js
// load the things we need
const mongoose = require('mongoose'),
    Schema = mongoose.Schema;

const bcrypt = require('bcrypt');
const crypto = require('crypto');

// define the schema for our user model
var userSchema = mongoose.Schema({
    email: String,
    emailHash: String, // required for changing password
    password: String,
    name: String,
    surname: String,
    salt: String,
    screenState: { type: String, default: null },
    role: { type: String, default: 'customer' }, // customer / root_admin ...
    session: String, // in case we want to expire all tokens
    locale: { type: String, default: 'en' },
    termsAndConditions: { type: Boolean, default: true },
    changePassword: {
        hash: { type: String },
        used: { type: Boolean, default: false },
        expires: { type: Number }, // timestamp
    },
    active: Boolean,
    availableSessionsHash: [{ type: String }],
    // active or pending (for self registering) / banned or terminated
    accountStatus: { type: String, default: 'active' },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now },
});

// methods ======================
// generating a hash
userSchema.methods.generateHash = function(password) {
    return bcrypt.hashSync(password, bcrypt.genSaltSync(8), null);
};

// checking if password is valid
userSchema.methods.validPassword = function(password, current_saved_hash) {
    return bcrypt.compareSync(password, current_saved_hash);
};

userSchema.methods.generateOneDirectionHash = function(word) {
    return crypto
        .createHash('sha256')
        .update(word)
        .digest('hex');
};

userSchema.methods.createSessionToken = function(userId, hash) {
    return userId + ':' + hash;
};

// for expiration hashes, for example
userSchema.methods.generateRandomHash = function() {
    let text = '';
    let possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

    for (var i = 0; i < 35; i++)
        text += possible.charAt(Math.floor(Math.random() * possible.length));

    return text;
};

// for expiration hashes, for example
userSchema.methods.hashRenewPasswordExpirationTime = function(timeInMinutes) {
    let oldDateObj = new Date();
    let newDateObj = new Date();
    newDateObj.setTime(oldDateObj.getTime() + timeInMinutes * 60 * 1000); // user has 20 minutes to change password

    return newDateObj.getTime();
};

// create the model for users and expose it to our app
module.exports = mongoose.model('User', userSchema);
