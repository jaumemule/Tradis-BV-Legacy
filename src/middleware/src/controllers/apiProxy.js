const _ = require('underscore');
const fs = require('fs');
const request = require('request');
const config = require('../config/apiProxy');

let self = (module.exports = {
    pass: function(req, res, next) {
        console.log(req.ip + ' - ' + req.method + ' - ' + req.url);
        const options = {
            uri: config.url + req.url,
            method: req.method,
            gzip: true,
            headers: {
                'client-id': 'secret',
                'client-secret': 'id',
                'Content-Type': 'application/json',
            },
        };

        if (!_.isEmpty(req.body)) {
            options.body = JSON.stringify(req.body);
        }

        request(options, function(err, httpResponse, body) {
            if (err) {
                console.log('proxy error', err);
                return res.status(500).send({ error: 'Unable to proxy request' });
            }

            if (body !== undefined && body !== '' && body !== null) {
                try {
                    body = JSON.parse(body, true);
                } catch (err) {
                    //
                }
            }

            res.proxyHttpResponse = httpResponse;
            res.proxyBody = body;

            next();
        });
    },

    sendFinalResponse: function(req, res, next) {
        res.status(res.proxyHttpResponse.statusCode).send(res.proxyBody);
    },
});
