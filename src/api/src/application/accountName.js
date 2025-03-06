
let self = module.exports = {
    generateFromUser: function(accountUniqueHash, userId) {
        return accountUniqueHash + '_' + userId
    }
}
