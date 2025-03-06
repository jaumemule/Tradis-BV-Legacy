const crypto = require('crypto');

// read https://gist.github.com/vlucas/2bd40f62d20c1d49237a109d491974eb if we need python support

let self = module.exports = {

    encrypt : function(stringToEncrypt, salt, iv) {

        let cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(salt), iv);
        let encrypted = cipher.update(stringToEncrypt);
       
        encrypted = Buffer.concat([encrypted, cipher.final()]);
       
        return iv.toString('hex') + ':' + encrypted.toString('hex');
    },
    
    decrypt : function(stringToDecrypt, salt) {
        let textParts = stringToDecrypt.split(':');
        let iv = Buffer.from(textParts.shift(), 'hex');
        let encryptedText = Buffer.from(textParts.join(':'), 'hex');
        let decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(salt), iv);
        let decrypted = decipher.update(encryptedText);
       
        decrypted = Buffer.concat([decrypted, decipher.final()]);
       
        return decrypted.toString();
    },

    createSalt: function(length = 32) {
        var result = '';
        var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var charactersLength = characters.length;
        for (var i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() * charactersLength));
        }
        return result;
    },

    createIv: function(length = 16) {
        return crypto.randomBytes(length);
    },
}
