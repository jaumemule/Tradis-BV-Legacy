const encrypter = require('../config/encrypt')
const crypto = require('crypto');

// NEVER COMMIT ANY UNENCRYPTED STRING
let keyString = ''
let secretString = ''
let passphraseString = ''

// DO NOT TOUCH
let salt = makeid(32)
let iv1 = crypto.randomBytes(16);

key = encrypter.encrypt(
    keyString, 
    salt,
    iv1
)

secret = encrypter.encrypt(
    secretString, 
    salt,
    iv1
)
    
passphrase = encrypter.encrypt(
    passphraseString, 
    salt,
    iv1
)

function makeid(length) {
    var result           = '';
    var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    var charactersLength = characters.length;
    for ( var i = 0; i < length; i++ ) {
       result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
 }
                     
console.log('salt', salt)
console.log('key', key)
console.log('secret', secret)
console.log('passphrase', passphrase)

decryptedVerifier = encrypter.decrypt(key, salt)
decryptedVerifierSecret = encrypter.decrypt(secret, salt)
console.log('----- verified decryption: -----', decryptedVerifier)
console.log('----- verified decryption: -----', decryptedVerifierSecret)