"use strict";
let self = module.exports = {
    
    client_secret   : 'id',
    client_id       : 'secret',

    verify : function( req, res, next ){

        let header_cs   = req.headers['client-secret'];
        let header_cid  = req.headers['client-id'];
        let self_cs     = self.client_secret;
        let self_cid    = self.client_id;
        let name        = req.params.name;
        
        if(header_cs === self_cs && header_cid === self_cid){

            next();

        } else {
            res.status(401).send({ data: { code: 'credentials_not_set', message:'API credentials not set or wrong'}});
        }
    },
};