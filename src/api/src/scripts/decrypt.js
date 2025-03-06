const encrypter = require('../config/encrypt')
const crypto = require('crypto');

// NEVER COMMIT ANY UNENCRYPTED STRING
let salt = ''

// let password = '$2b$08$aVfR0Dypt2cHpgIo5dfQruoVl0lr/YiPKAYI470abe7FXndq7vdmC'
let key = ':'
let secret = ':'
let passphrase = ':'

decKey = encrypter.decrypt(key, salt)
decsec = encrypter.decrypt(secret, salt)
decpass = encrypter.decrypt(passphrase, salt)
console.log('----- verified decryption: -----', decKey)
console.log('----- verified decryption: -----', decsec)
console.log('----- verified decryption: -----', decpass)
