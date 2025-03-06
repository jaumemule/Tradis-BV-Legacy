'use strict';

let self = (module.exports = {
    __backwardsCompatibleFirstBalanceResults: function(firstBalance, cb) {
        if (
            typeof firstBalance.baseCoinAmount === 'undefined' &&
            typeof firstBalance.totalUSDBeforeTrading !== 'undefined'
        ) {
            let firstBalanceInBaseCoin = firstBalance.totalUSDBeforeTrading;
            let firstBalanceInBitcoin = firstBalance.totalBtcBeforeTrading;
            cb(firstBalanceInBaseCoin, firstBalanceInBitcoin);
        } else if (typeof firstBalance.baseCoinAmount !== 'undefined') {
            let firstBalanceInBaseCoin = firstBalance.baseCoinAmount;
            let firstBalanceInBitcoin = firstBalance.bitcoinAmount;
            cb(firstBalanceInBaseCoin, firstBalanceInBitcoin);
        } else {
            cb(null, null);
        }
    },
    __secondReleaseMapping: function(balanceState, firstBalance, cb) {
        if (typeof firstBalance._strategy !== 'undefined') {
            let profit = {};

            for (let coin in firstBalance.totals) {
                let currentCoinBalance = balanceState.totalBalanceInEveryCoinDict[coin];
                let firstCoinBalance = firstBalance.totals[coin];
                let percentage = ((currentCoinBalance - firstCoinBalance) / firstCoinBalance) * 100;
                profit[coin] = parseFloat(percentage.toFixed(2));
            }

            cb({
                balances: balanceState.activeBalancesForStrategyDict,
                totals: balanceState.totalBalanceInEveryCoinDict,
                initialBalances: {
                    date: firstBalance.at,
                    balances: firstBalance.balances,
                    totals: firstBalance.totals,
                },
                percentageOfProfit: profit,
                signals: balanceState.signals,
                baseCoin: balanceState.baseCoin,
                exchangeRates: balanceState.exchangeRate,
            });
        } else {
            // still on first data format (legacy procyon)
            cb(null);
        }
    },
    computeProfit: (req, res, next) => {
        let firstBalance = res.firstBalanceProxyResponse;
        let balance = res.balanceProxyResponse;
        let exchangeRates = res.exchangeRatesProxyResponse;
        let balanceState = res.balanceStateProxyResponse;

        // THIS IS LEGACY, FOR BACKWARDS COMPATIBILITY
        self.__backwardsCompatibleFirstBalanceResults(firstBalance, function(
            firstBalanceInBaseCoin,
            firstBalanceInBitcoin,
        ) {
            // set internval variables
            let currentBalanceInBaseCoin = balance[req.params.baseCoin];
            let currentBalanceInBitcoin = balance.BTC;
            let currentBitCoinExchangeRate = exchangeRates['BTC']['p'];

            self.__secondReleaseMapping(balanceState, firstBalance, function(balanceStateValue) {
                // compute current balances
                let currentTotalBalanceInBaseCoin =
                    currentBalanceInBaseCoin + currentBalanceInBitcoin * currentBitCoinExchangeRate;

                let currentTotalBalanceInBitcoin =
                    currentBalanceInBitcoin + currentBalanceInBaseCoin / currentBitCoinExchangeRate;

                // compute profit
                let profitPercentageInBaseCoin =
                    ((currentTotalBalanceInBaseCoin - firstBalanceInBaseCoin) /
                        firstBalanceInBaseCoin) *
                    100;
                let profitPercentageInBitcoin =
                    ((currentTotalBalanceInBitcoin - firstBalanceInBitcoin) /
                        firstBalanceInBitcoin) *
                    100;

                return res.status(200).send({
                    baseCoinPercentageProfit: profitPercentageInBaseCoin,
                    bitcoinPrecentageProfit: profitPercentageInBitcoin,

                    basecoinCurrentBalance: currentTotalBalanceInBaseCoin,
                    bitcoinCurrentBalance: currentTotalBalanceInBitcoin,

                    baseCoinInitialBalance: firstBalanceInBaseCoin,
                    bitcoinInitialBalance: firstBalanceInBitcoin,

                    // second release
                    balanceState: balanceStateValue,
                });
            });
        });
    },
});
