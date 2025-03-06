// server.js

// set up ======================================================================
// get all the tools we need
const express       = require('express')
 , app              = express()
 , port             = process.env.PORT || 8060
 , bodyParser       = require('body-parser')
 , mongoose         = require('mongoose')
 , compression      = require('compression')

 // services ======================================================================
 , configDB         = require('./src/config/database.js')
 , redisConnection  = require('./src/config/redisConnection')
 , AccountsInMemoryContainer = require('./src/infra/accountsInMemoryContainer')

// configuration ===============================================================
mongoose.connect(configDB.url, { useNewUrlParser: true, useCreateIndex: true, useUnifiedTopology: true, useFindAndModify: false }); // connect to our database
redisConnection.stablish() // redis connection
AccountsInMemoryContainer.listen()

app.use(compression());

app.use(bodyParser.json({strict: true}));
app.use(bodyParser.urlencoded({extended: true}));

app.use(function(req, res, next) {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

process.env.TZ = 'utc'

app.set('view engine', 'ejs');
// routes ======================================================================
require('./src/routes.js')(app); // load our routes

// launch ======================================================================
app.listen(port);
console.log('The magic happens on port ' + port);