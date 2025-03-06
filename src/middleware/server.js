// server.js

// set up ======================================================================
// get all the tools we need
const express = require('express');
const app = express();
const port = process.env.PORT || 8071;
const bodyParser = require('body-parser');
const compression = require('compression');
const cors = require('cors');
const mongoose = require('mongoose');
const configDB = require('./src/config/database.js');

// configuration ===============================================================
mongoose.connect(configDB.url, {
    useNewUrlParser: true,
    useCreateIndex: true,
    useUnifiedTopology: true,
}); // connect to our database

app.use(compression());
app.use(cors());
app.use(bodyParser.json({ strict: true }));
app.use(bodyParser.urlencoded({ extended: true }));

// TODO limit this in production
app.use(function(req, res, next) {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

process.env.TZ = 'utc';

// routes ======================================================================
require('./src/routes.js')(app); // load our routes

// launch ======================================================================
app.listen(port);
console.log('The magic happens on port ' + port);
