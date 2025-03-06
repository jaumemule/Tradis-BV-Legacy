let self = (module.exports = {
    userAccounts: function(req, res, next) {
        req.url = '/api/v1/accounts/users/' + req.body.userSession.uid;
        next();
    },
    userAccountsFirstBalance: function(req, res, next) {
        req.url = '/api/v1/accounts/first-balance/' + req.params.accountId;
        next();
    },

    // deprecate this after procyon in favour of balance state
    userAccountBalance: function(req, res, next) {
        req.url = '/api/v1/wallet/balances?cached=1';
        req.method = 'POST';
        req.body = [
            {
                exchangeName: req.params.exchangeName,
                account: req.params.accountName,
                singleRequest: true,
            },
        ];
        next();
    },
    userAccountBalanceState: function(req, res, next) {
        req.url = '/api/v1/account-balance-state/' + req.params.accountId;
        req.method = 'GET';
        next();
    },
    currentExchangeRates: function(req, res, next) {
        let datetime = new Date(Date.now() - 1000 * 180); // with three max minutes (in case we are missing)
        req.url =
            '/api/v1/exchange-rates/' +
            req.params.exchangeName +
            '/' +
            req.params.baseCoin +
            '?after=' +
            datetime;
        next();
    },
    restartAccountProfitCalculation: function(req, res, next) {
        req.url =
            '/api/v1/accounts/' +
            req.params.accountId +
            '/restart-profit-calculation/strategies/' +
            req.params.strategyId;
        next();
    },
    swapStrategy: function(req, res, next) {
        req.url = '/api/v1/accounts/' + req.params.accountId + '/swap-strategy';
        next();
    },
    unlinkStrategies: function(req, res, next) {
        req.url = '/api/v1/accounts/' + req.params.accountId + '/unlink-strategies';
        next();
    },
    mutateAccountState: function(req, res, next) {
        req.url = '/api/v1/accounts/state/' + req.params.accountId;
        next();
    },
});
