const adminLoginController = require('./controllers/admin-login');
const userRegistrationController = require('./controllers/user-registration');
const userAccountController = require('./controllers/user-account');
const apiProxyController = require('../src/controllers/apiProxy');
const userTokenVerification = require('../src/application/userToken');
const rewriteInteralApiRequest = require('../src/application/rewriteInteralApiRequest');
const rewriteInteralApiResponse = require('../src/application/rewriteInteralApiResponse');
const loginAttemptsMiddleware = require('../src/application/loginAttemptsMiddleware');
const passport = require('passport');
const passportOptions = { session: false };

require('./middlewares/passport')(passport);

module.exports = function(app) {
    // MIDDLEWARE PUBLIC SERVICES
    // MIDDLEWARE PUBLIC SERVICES
    // MIDDLEWARE PUBLIC SERVICES

    app.get('/api/v1/health', (req, res) => res.send('OK'));
    app.get('/api/v1/is-max-users-achieved', userRegistrationController.isMaxUsersAchieved);
    app.get(
        '/api/v1/strategies',
        apiProxyController.pass,
        rewriteInteralApiResponse.strategies,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/strategy-results/plot/:strategyName',
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    // MIDDLEWARE AUTHENTICATION SERVICES
    // MIDDLEWARE AUTHENTICATION SERVICES
    // MIDDLEWARE AUTHENTICATION SERVICES
    app.post('/api/v1/admin-login', adminLoginController.login);
    app.post(
        '/api/v1/user-registration',
        loginAttemptsMiddleware.isUserReachingTheLimitOfRegistrationAttempts,
        userRegistrationController.register,
    );
    app.get(
        '/api/v1/user-registration-confirmation/:userId/:hash',
        userRegistrationController.registerConfirm,
    );

    app.post('/api/v1/change-password-generate', userRegistrationController.changePasswordGenerate);
    app.post(
        '/api/v1/change-password-confirmation/:userId/:hash',
        userRegistrationController.changePasswordConfirm,
    );

    app.post(
        '/api/v1/user-login',
        loginAttemptsMiddleware.isUserReachingTheLimitOfLoginAttempts,
        userRegistrationController.login,
    );
    app.post(
        '/api/v1/user-logout',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        userRegistrationController.logout,
    );

    app.patch(
        '/api/v1/user-screen-state',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        userRegistrationController.updateScreenState,
    );
    app.get(
        '/api/v1/user-screen-state',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        userRegistrationController.getScreenState,
    );

    // PORTAL PROXY USER SERVICES
    // PORTAL PROXY USER SERVICES
    // PORTAL PROXY USER SERVICES
    app.get(
        '/api/v1/user-accounts',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.userAccounts,
        apiProxyController.pass,
        rewriteInteralApiResponse.userAccounts,
        apiProxyController.sendFinalResponse,
    );

    app.post(
        '/api/v1/user-accounts',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.userAccounts,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.patch(
        '/api/v1/user-accounts/:accountId/restart-profit-calculation/strategies/:strategyId',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.restartAccountProfitCalculation,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.patch(
        '/api/v1/user-accounts/:accountId/unlink-strategies',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.unlinkStrategies,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.patch(
        '/api/v1/user-accounts/:accountId/swap-strategy',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.swapStrategy,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.patch(
        '/api/v1/user-accounts/state/:accountId',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.mutateAccountState,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/user-accounts/first-balance/:accountId',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.userAccountsFirstBalance,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/user-accounts/profit/:accountId/:accountName/:exchangeName/:baseCoin',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,

        rewriteInteralApiRequest.userAccountsFirstBalance,
        apiProxyController.pass,
        rewriteInteralApiResponse.userAccountsFirstBalanceStoreInMemory,
        rewriteInteralApiRequest.currentExchangeRates,
        apiProxyController.pass,
        rewriteInteralApiResponse.currentExchangeRates,
        rewriteInteralApiResponse.currentExchangeRatesStoreInMemory,
        rewriteInteralApiRequest.userAccountBalance,
        apiProxyController.pass,
        rewriteInteralApiResponse.accountBalance,
        rewriteInteralApiResponse.userAccountBalanceStoreInMemory,

        rewriteInteralApiRequest.userAccountBalanceState,
        apiProxyController.pass,
        rewriteInteralApiResponse.accountBalanceStoreInMemory,

        userAccountController.computeProfit,
    );

    app.get(
        '/api/v1/user-accounts/:accountName/:exchangeName/balance',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.userAccountBalance,
        apiProxyController.pass,
        rewriteInteralApiResponse.accountBalance,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/current-exchange-rates/:exchangeName/:baseCoin',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        rewriteInteralApiRequest.currentExchangeRates,
        apiProxyController.pass,
        rewriteInteralApiResponse.currentExchangeRates,
        apiProxyController.sendFinalResponse,
    );

    // PROXY ADMIN SERVICES
    // PROXY ADMIN SERVICES
    // PROXY ADMIN SERVICES

    app.get(
        '/api/v1/coins',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );
    app.post(
        '/api/v1/coins',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.patch(
        '/api/v1/coins/:id',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );
    app.post(
        '/api/v1/coins/soft-lock/:coinName',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/strategies',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );
    app.get(
        '/api/v1/strategies/:strategyName',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );
    app.post(
        '/api/v1/strategies',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );
    app.patch(
        '/api/v1/strategies/:strategyName',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/strategy-results/:strategyName/profitability',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.patch(
        '/api/v1/strategy-results/:strategyName/profitability',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/trading/lock/:strategyName/:mode',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/trading/unlock/:strategyName/:mode',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/wallet/balances',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/strategy-results/:strategyName/percentage-of-profit-from-date',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/time',
        passport.authenticate('jwt', passportOptions),
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    // administration
    // only admin users are allowed to take action here
    app.get(
        '/api/v1/admin/accounts',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        userTokenVerification.verifyAdminRootRole,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.get(
        '/api/v1/admin/users',
        userTokenVerification.verifyTokenAndSetDecryptedUserToRequestObject,
        userTokenVerification.verifyAdminRootRole,
        apiProxyController.pass,
        apiProxyController.sendFinalResponse,
    );

    app.use(function(req, res) {
        res.status(404).send({ data: { message: 'Document not found', code: 'general_404' } });
    });

    app.use(function(err, req, res, next) {
        console.error('error: ', err);
        res.status(500).send({ data: { code: 'system_error', message: 'Something bad happened' } });
    });
};
