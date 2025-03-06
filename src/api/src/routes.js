const coins = require('../src/controllers/coins');
const strategies = require('../src/controllers/strategies');
const coinsPrices = require('../src/controllers/coinsPrices');
const migrations = require('../src/controllers/migrations');
const wallet = require('../src/controllers/wallet');
const credentials = require('../src/middlewares/apiCredentials');
const strategyResults = require('../src/controllers/strategy-results');
const trading = require('../src/controllers/trading');
const trades = require('../src/controllers/trades'); // account results
const accounts = require('../src/controllers/accounts');
const users = require('../src/controllers/users');
const accountsValidation = require('../src/application/accountValidation');

module.exports = function(app) {

  app.get('/api/v1/health', function(req,res){
    res.send("OK");
  });

  app.copy('/api/v1/migrate-daily', credentials.verify, migrations.daily);
  app.delete('/api/v1/remove-old-live-data', credentials.verify, migrations.removeSeveralDaysOfMainCollection);
  
  app.post('/api/v1/wallet/balances', credentials.verify, wallet.balances);
  app.post('/api/v1/wallet/deposits', credentials.verify, wallet.deposits);
  app.post('/api/v1/wallet/withdrawals', credentials.verify, wallet.withdrawals);
  app.post('/api/v1/wallet/trades', credentials.verify, wallet.trades);
  app.post('/api/v1/wallet/buy', credentials.verify, wallet.buy);
  app.post('/api/v1/wallet/sell', credentials.verify, wallet.sell);
  app.post('/api/v1/wallet/open-orders', credentials.verify, wallet.openOrders);
  app.post('/api/v1/wallet/cancel-orders', credentials.verify, wallet.cancelOrders);

  app.get('/api/v1/coins', credentials.verify, coins.get);
  app.post('/api/v1/coins', credentials.verify, coins.create);
  app.patch('/api/v1/coins/:id', credentials.verify, coins.update);

  app.get('/api/v1/coins/soft-lock', credentials.verify, coins.lockedCoinsPerStrategy);
  app.post('/api/v1/coins/soft-lock/:coinName', credentials.verify, coins.softLockForStrategy);
  app.delete('/api/v1/coins/soft-lock/:coinName', credentials.verify, coins.softUnlockCoinForAllStrategies);
  
  app.get('/api/v1/strategies', credentials.verify, strategies.get);
  app.get('/api/v1/strategies/:strategyName', credentials.verify, strategies.getById);
  app.post('/api/v1/strategies', credentials.verify, strategies.create);
  app.patch('/api/v1/strategies/:strategyName', credentials.verify, strategies.update);


  // DEPRECATED
  app.get('/api/v1/strategy-results/:strategyName/profitability', credentials.verify, strategyResults.profitabilityPerStrategy);
  // DEPRECATED
  app.get('/api/v1/strategy-results/:strategyName/percentage-of-profit-from-date', credentials.verify, strategyResults.percentageOfProfitability);
  app.get('/api/v1/strategy-results/plot/:strategyName', credentials.verify, strategyResults.results);

  app.get('/api/v1/trading/lock/:strategyName/:mode', credentials.verify, trading.lock);
  app.get('/api/v1/trading/unlock/:strategyName/:mode', credentials.verify, trading.unlock);

  app.get('/api/v1/time', credentials.verify, trading.time);

  app.get('/api/v1/accounts', credentials.verify, accounts.all);
  app.get('/api/v1/accounts/:strategyId', credentials.verify, accounts.byStrategyId);

  app.patch('/api/v1/disable-account/:accountName', credentials.verify, accounts.disable);  // DEPRECATED, USE STATE INSTEAD
  app.patch('/api/v1/accounts/state/:accountId', credentials.verify, accounts.mutateState);

  app.get('/api/v1/accounts/first-balance/:accountId', credentials.verify, trades.calculationStartingPoint);
  app.get('/api/v1/account-balance-state/:accountId', credentials.verify, trades.getBalanceState);

  app.patch('/api/v1/accounts/:accountId/restart-profit-calculation/strategies/:strategyId', credentials.verify, trades.restartResultCalculationPoint);

  app.patch('/api/v1/accounts/:accountId/swap-strategy', credentials.verify, accounts.swapStrategy);
  app.patch('/api/v1/accounts/:accountId/unlink-strategies', credentials.verify, accounts.removeStrategyLink);

  app.post('/api/v1/accounts/users/:userId', credentials.verify, accountsValidation.validateCredentialsMiddleware, accounts.create);
  app.get('/api/v1/accounts/users/:userId', credentials.verify, accounts.byUserId);

  // TODO generalize and sanitise request. Supports only binance in USDT
  app.get('/api/v1/exchange-rates/:exchangeName/:baseCoin', credentials.verify, coinsPrices.exchangeRates);

  // administration
  app.get('/api/v1/admin/accounts', credentials.verify, accounts.listWithUsers);
  app.get('/api/v1/admin/users', credentials.verify, users.listWithWallets);

  app.use(function(req, res) {
     res.status(404).send({data: {message: 'Document not found', code: 'general_404'}});
  });

  app.use(function (err, req, res, next) {
    console.error('error: ', err)
    res.status(500).send({ data: {code: 'system_error', message: 'Something bad happened'}});
  });
};
