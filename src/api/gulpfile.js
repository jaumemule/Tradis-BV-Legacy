let gulp = require('gulp');
let configDB = require('./src/config/database.js');
let mongoose = require('mongoose');
let fixtures = require('./src/fixtures/fixtures.js');

gulp.task('coins', function (cb) {
    
    if(process.env.environment === 'dev'){
        let mongo = configDB.url
        mongoose.connect(configDB.url, { useNewUrlParser: true, useCreateIndex: true }); // connect to our database 
    } else {
        // FIX FOR PRODUCTION, CAN'T READ ENV VARS
        let mongo = 'mongodb://tradis-staging:xxxxxx/aggregated?replicaSet=rs-ds129605'
        mongoose.connect(mongo, { useNewUrlParser: true, useCreateIndex: true }); // connect to our database 
    }
 
    fixtures.coinsListWithPercentages(function( ){
        console.log('FIXTURES have been created for coins list', process.env.environment );
        cb()
    }, function() {
        console.log('FIXTURES already exists for coins list', process.env.environment );
        cb()
    });
});

gulp.task('strategies', function (cb) {

    if(process.env.environment === 'dev'){
        let mongo = configDB.url
        mongoose.connect(configDB.url, { useNewUrlParser: true, useCreateIndex: true }); // connect to our database 
    } else {
        // FIX FOR PRODUCTION, CAN'T READ ENV VARS
        let mongo = 'mongodb://tradis-staging:xxxxxx/aggregated?replicaSet=rs-ds129605'
        mongoose.connect(mongo, { useNewUrlParser: true, useCreateIndex: true }); // connect to our database 
    }

    fixtures.strategies(function( ){
        console.log('FIXTURES have been created for strategies', process.env.environment );
        cb()
    }, function() {
        console.log('FIXTURES already exists for strategies', process.env.environment );
        cb()
    });
});

gulp.task('default', [ 'coins', 'strategies'], function(){
    process.exit()
});
