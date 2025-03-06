// app/models/user.js
// load the things we need
var mongoose = require('mongoose'),
    Schema = mongoose.Schema;

// define the schema for our user model
var userSchema = mongoose.Schema({
    email: String,
    emailHash: String, // required for changing password
    password: String,
    name: String,
    surname: String,
    salt: String,
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

// create the model for users and expose it to our app
module.exports = mongoose.model('User', userSchema);
