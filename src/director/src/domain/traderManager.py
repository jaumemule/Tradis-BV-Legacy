from typing import List, Any, Dict
import numpy as np
import pandas as pd

class TraderManager:

    isStrategyLockedToTrade: bool
    coinsWithMoney: List[Any]
    current_money_in_btc: float
    moveAllToTUSD: bool

    def __init__(self, environmentConfigurations, ApiClient, Slack):
        self.previousInvestmentWithCurrentCoinValue = {}
        self.environmentConfigurations = environmentConfigurations
        self.apiClient = ApiClient
        self.slack = Slack
        self.extraMessage = ''
        self.moveAllToTUSD = 0
        self.isStrategyLockedToTrade = False

    # TODO DEPRECATED
    def calculateCurrentMoneyInWeHaveInTheWalletInBtc(self, balances_and_prices_df):

        # We multiply row balances with userAccountList to btc to have all amounts in BTC
        balances_and_prices_df["btc_balance"] = balances_and_prices_df["balances"].astype(float) * balances_and_prices_df["trade"].astype(float)
        # We order the balances to get the five highest (in BTC)
        #balances_and_prices_df.sort_values(by="btc_balance", axis=0, ascending=False, inplace=True)

        # @TODO we don't need this now, but would be nice to track
        # we should extract this loggers
        total_btc = balances_and_prices_df["btc_balance"].sum()

        return total_btc

    # THIS will give the candidates to be sold or stored to the current investments
    def currentInvestments(self, balances_and_prices_df, unserialized_tracker_data, accountsContainer, accountName, base_coin='BTC'):
        # check if USDT is the only coin with money
        countTotalCoinsWithMoney = 0
        self.coinsWithMoney = []
        # if so, then we sell all we have on any currency

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        minAmountToTrade = self.environmentConfigurations.minimAmountToTradeInDollars

        coins_to_trade_in_strategy = list(unserialized_tracker_data.keys())

        # We need to reorder the dataframe to create the selling orders correctly (I think)

        balances_and_prices_df.sort_values('btc_balance', inplace=True, ascending=False)
        quantityInDollars = 0

        for index, row in balances_and_prices_df.iterrows():

            quantity = row["balances"] # this is BTC

            # TODO This is a disaster. runOnBasedCurrency is not unique anymore, therefore we are repeating exceptions
            if base_coin == "BTC" and index == 'BTC':
                quantityInDollars = quantity / float(unserialized_tracker_data['TUSD']["p"])

            elif base_coin == "BTC" and index == 'TUSD':
                quantityInDollars = quantity

            if base_coin in fallbackCoins and index not in fallbackCoins:
                quantityInDollars = quantity / float(unserialized_tracker_data[base_coin]["p"])

            elif base_coin in fallbackCoins and index in fallbackCoins:
                quantityInDollars = quantity

            else:
                if index in unserialized_tracker_data:
                    quantityInDollars = quantity * (float(unserialized_tracker_data[index]["p"])) / (unserialized_tracker_data['TUSD']["p"])

            if self.environmentConfigurations.currentlyRunningMethodology == "real_money" and index in unserialized_tracker_data:
                if quantityInDollars > minAmountToTrade and index not in ['BTC', 'BNB', 'ETH']:  # IGNORE BNB, used for fees
                    countTotalCoinsWithMoney += 1
                    self.coinsWithMoney.append(index)
                # for statistics TODO move this calculations to another class, this is a coupled dependency

            elif quantityInDollars > 0 and index in unserialized_tracker_data:
                countTotalCoinsWithMoney += 1
                self.coinsWithMoney.append(index)

            # we don't trade less than 10 euros of BTC (hold to BTC). leave also a 5% margin to prevent collisions
            config_method = self.environmentConfigurations.currentlyRunningMethodology
            if config_method == "real_money" and index in coins_to_trade_in_strategy and index not in base_coin:

                # FIXME: this might collide with a similar condition in line 331 (self.minimum_amount_check())

                countTotalCoinsWithMoney += 1
                self.coinsWithMoney.append(index)

            if index in unserialized_tracker_data:
                previousInvestmentWithCurrentCoinValue = {}
                previousInvestmentWithCurrentCoinValue[index] = unserialized_tracker_data[index]["p"]
                accountsContainer.addResult(accountName, 'previousInvestmentWithCurrentCoinValue', previousInvestmentWithCurrentCoinValue)

        return countTotalCoinsWithMoney, self.coinsWithMoney

    def extractLockedCoinsFromBuyList(self, buyList, strategyName):
        softLockedCoins = self.apiClient.retrieveSoftLockedCoins()

        lockedCoins = []
        # TODO move this into the client
        for lockedCoin in softLockedCoins:
            if strategyName in lockedCoin['strategy']:
                lockedCoins.append(lockedCoin['coin'])

        for buyingCoin in buyList:
            if buyingCoin in lockedCoins:
                # TODO interesting metric
                buyList.remove(buyingCoin)
                self.extraMessage += ' (did not buy ' + str(buyingCoin) + ' because is still locked) '

        return buyList

    def serialiseSellOrders(
            self,
            balances_and_prices_df,
            unserialized_tracker_data: object,
            sellCoins: dict,
            exchange_markets: list,
            accountName,
            base_coin='BTC'
    ) -> object:

        fees = {"BNB" : 0.00075, "BTC" : 0.001, "ETH" : 0.001, "TUSD" : 0.00075, 'USDT': 0.001, 'USD': 0.001, 'EUR': 0.001}

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        # There is a problem in the logic behind this and the next function, and is that they are
        # duplicating logic from the create_trading_df methodology, thus leading to incorrections and errors
        # FIXME: they have to be merged

        sell_orders = {}
        sell_orders[accountName] = []

        if self.environmentConfigurations.currentlyRunningMethodology == self.environmentConfigurations.runMethodologyProduction:
            ico = ":dart:"
            message = ico + " Director is selling "
        else:
            ico = ":desert_island:"
            message = ico + " Sand director is selling "

        total_quantity = 0

        for selling_coin, values in sellCoins.items():

            market_currency = exchange_markets[selling_coin]['market']
            transaction_amount_in_target_currency = values['quantity']
            btc_to_add = transaction_amount_in_target_currency * balances_and_prices_df['trade'][selling_coin]

            if selling_coin != market_currency: # IGNORE stuff like BTC/BTC

                if base_coin == 'BTC':
                    quantityInDollars = transaction_amount_in_target_currency * (float(unserialized_tracker_data[selling_coin]["p"])) / (float(unserialized_tracker_data['TUSD']["p"]))
                elif base_coin in fallbackCoins:
                    quantityInDollars = transaction_amount_in_target_currency * (float(unserialized_tracker_data[selling_coin]["p"])) / (float(unserialized_tracker_data[base_coin]["p"]))
                else:
                    raise NotImplementedError('base coin not implemented')

                if transaction_amount_in_target_currency <= 0:
                    continue

                config_method = self.environmentConfigurations.currentlyRunningMethodology
                if config_method == "real_money" and quantityInDollars < self.environmentConfigurations.minimAmountToTradeInDollars:
                    # self.slack.send('Trying to sell ' + str(quantityInDollars) + ' dollars in ' + selling_coin + ', but not enough to trade')
                    continue

                sell_orders[accountName].append({"targetCurrency": market_currency, "baseCurrency": selling_coin, "quantity": transaction_amount_in_target_currency})
                balances_and_prices_df.loc[selling_coin, "balances"] -= transaction_amount_in_target_currency

                if self.environmentConfigurations.currentlyRunningMethodology != self.environmentConfigurations.runMethodologyProduction:
                    transaction_amount_in_other_currency = float(btc_to_add) / float(balances_and_prices_df.loc[market_currency, 'trade'])
                    balances_and_prices_df.loc[market_currency,"balances"] += transaction_amount_in_other_currency * (1 - fees[market_currency])

                message += str(transaction_amount_in_target_currency) + " " + selling_coin + " via " + selling_coin + "/" + market_currency + " trade pair \n"
                total_quantity += transaction_amount_in_target_currency

        if self.environmentConfigurations.currentlyRunningMethodology != self.environmentConfigurations.runMethodologyProduction:
            # We recompute the balances in BTC
            balances_and_prices_df["btc_balance"] = balances_and_prices_df["balances"].astype(float) * balances_and_prices_df["trade"].astype(float)

        if(len(sell_orders[accountName])) == 0 or total_quantity == 0:
            message = ico + " Holding all balances. Nothing interesting to sell"

        if self.isStrategyLockedToTrade == True:
            message += " \n\n :lock: Strategy is locked to trade: all moved to TUSD, will make the strategy unactive :lock:\n\n"

        return sell_orders, self.round_numbers(balances_and_prices_df), message

    def serialiseBuyOrders(
            self,
            balances_and_prices_df,
            unserialized_tracker_data: list,
            buyCoins: dict,
            exchange_markets: object,
            accountName,
            base_coin='BTC'
    ) -> object:
        fees = {"BNB" : 0.00075, "BTC" : 0.001,  "ETH" : 0.001, "TUSD" : 0.00075, 'USDT': 0.001, 'EUR': 0.001, 'USD': 0.001}

        # There is a problem in the logic behind this and the previous function, and is that they are
        # duplicating logic from the create_trading_df methodology, thus leading to incorrections and errors
        # FIXME: they have to be merged

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        buy_orders = {}
        buy_orders[accountName] = []

        if self.environmentConfigurations.currentlyRunningMethodology == self.environmentConfigurations.runMethodologyProduction:
            ico = ":dart:"
            message = ico + " Director is buying "
        else:
            ico = ":desert_island:"
            message = ico + " Sand director is buying "

        total_balance_in_base_coin = balances_and_prices_df.loc[:, "btc_balance"].sum()

        # TUSD is tethered to USD, so we assume that if the AI predicts this to increase it means the others are decreasing,
        # and this usually means all others decrease. Therefore, we back everything up in TUSD
        # This can be relaxed into only doing it when TUSD is the highest predicted, or two highest, otherwise I'm afraid
        # the director will be way too lazy. It would be:
        # if "TUSD" in buyCoins[0][0]:

        total_quantity = 0

        if total_balance_in_base_coin < 0:
            message = ico + " Not enough balance to perform any buy operation "
            return buy_orders, balances_and_prices_df, message

        counter = 0
        for coin, values in buyCoins.items():

            marketCoin = values['market']

            if coin == marketCoin: # IGNORE stuff like BTC/BTC
                continue

            # TODO hardcoding alert: we should be able to trade in other markets
            #transaction_quantity_in_btc = total_btc * new_percentages[counter]
            counter+=1

            transaction_amount_in_target_currency = values['quantity']
            transaction_quantity_in_btc = transaction_amount_in_target_currency * float(unserialized_tracker_data[coin]["p"])

            if base_coin == 'BTC':
                quantityInDollars = transaction_quantity_in_btc / (float(unserialized_tracker_data['TUSD']["p"]))
            elif base_coin in fallbackCoins:
                quantityInDollars = transaction_quantity_in_btc / (float(unserialized_tracker_data[base_coin]["p"]))
            else:
                raise NotImplementedError('base coin not existant')

            if transaction_amount_in_target_currency <= 0:
                continue

            config_method = self.environmentConfigurations.currentlyRunningMethodology
            if config_method == "real_money" and quantityInDollars < self.environmentConfigurations.minimAmountToTradeInDollars:
                # self.slack.send('Trying to buy ' + str(quantityInDollars) + ' dollars in ' + coin + ', but not enough to trade')
                continue

            # APPLY SLIPPAGE FORMULA
            if config_method == "real_money":

                # LEAVE ALWAYS % OF MONEY TO PREVENT SLIPPAGE ISSUES
                # TODO move this somewhere else, is reusable
                if self.environmentConfigurations.currentlyRunningMethodology == "real_money":
                    slippageReservationInPercentage = self.environmentConfigurations.slippageSecurityMarginInPercentage  # dollars
                    transaction_amount_in_target_currency = transaction_amount_in_target_currency - (transaction_amount_in_target_currency * (slippageReservationInPercentage / 100))

            buy_orders[accountName].append({"targetCurrency": marketCoin,
                                          "baseCurrency": coin,
                                          "quantity": transaction_amount_in_target_currency})

            if self.environmentConfigurations.currentlyRunningMethodology != self.environmentConfigurations.runMethodologyProduction:
                balances_and_prices_df = self.round_numbers(balances_and_prices_df)
                balances_and_prices_df.loc[coin, "balances"] += (transaction_amount_in_target_currency * (1 - fees[marketCoin])) # include amount to the target coin
                amount_in_own_currency = float(balances_and_prices_df.loc[marketCoin, 'btc_balance']) / float(balances_and_prices_df.loc[marketCoin, 'trade'])
                balances_and_prices_df.loc[marketCoin, "btc_balance"] -= transaction_quantity_in_btc # remove BTC amount
                balances_and_prices_df.loc[marketCoin, "balances"] -= amount_in_own_currency  # remove own currency amount
                balances_and_prices_df.loc[:, "btc_balance"] = balances_and_prices_df["balances"].astype(float) * balances_and_prices_df["trade"].astype(float)
            message += str(transaction_amount_in_target_currency) + " " + coin + " via " + coin + "/" + marketCoin + " trade pair \n"
            total_quantity += transaction_amount_in_target_currency

        # I put btc to zero to avoid things like 10^13 - I don't explicitely set it to zero in case there are bugs that
        # make it bigger than 0.
        # balances_and_prices_df.loc["BTC", "balances"] = round(balances_and_prices_df.loc["BTC", "balances"], 7)

        # We recompute the balances again
        balances_and_prices_df["btc_balance"] = balances_and_prices_df["balances"].astype(float) * balances_and_prices_df["trade"].astype(float)

        if (len(buy_orders[accountName])) == 0 or total_quantity == 0:
            message = ico + " Holding all balances. Nothing interesting to buy "

        if self.moveAllToTUSD == 1:
            message = ico + " on buy: TUSD on a high prediction. All moved to TUSD. (withdraw?) "

        message += ' ' + self.extraMessage

        return buy_orders, self.round_numbers(balances_and_prices_df), message

    def generate_trading_input_object(self, predictions, balances_and_prices_df, current_balances, tracker_data, strategy, accountName, accountsContainer):

        baseCoin = strategy['baseCoin']
        coins_that_strategy_trades = [*strategy['exchangeMarkets']]

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        # TODO remove this hardcodes and assumptions
        if baseCoin == 'BTC':
            if len(predictions) == 0:
                self.slack.send("TUSD is the only prediction")
                predictions = ['TUSD']

            self.isStrategyLockedToTrade = False
            if strategy['activelyTrading'] == False:
                predictions = ['TUSD']
                self.isStrategyLockedToTrade = True

        if baseCoin in fallbackCoins:
            if len(predictions) == 0:
                predictions = []

            self.isStrategyLockedToTrade = False

            if strategy['activelyTrading'] == False:
                predictions = [strategy['baseCoin']]
                self.isStrategyLockedToTrade = True

        countTotalCoinsWithMoney, coinsToTrade = self.currentInvestments(
            balances_and_prices_df,
            tracker_data,
            accountsContainer,
            accountName,
            strategy['baseCoin']
        )

        predictions = self.extractLockedCoinsFromBuyList(
            predictions,
            strategy['strategyName']
        )

        obj = {}
        obj['new_predictions'] = predictions
        obj['actual_investments'] = {}

        for coin in coinsToTrade:
            # setattr(obj, coin, 1)
            # if current_balances["balances"][coin] in coins_that_strategy_trades:
            obj['actual_investments'][coin] = {}
            obj['actual_investments'][coin]['quantity'] = current_balances["balances"][coin]

        return obj, self.serialise_tracker_prices(tracker_data)

    def serialise_tracker_prices(self, tracker_prices):

        pricePerCoin = {}
        for key, price in tracker_prices.items():
            if key != 'date' and key != '_id':
                pricePerCoin[key] = {}
                pricePerCoin[key] = float(price['p'])

        return pricePerCoin

    def create_trading_df(self, predictions, wallet_state, pricePerCoin, exchange_markets, accountName, accountsContainer, revertMarket = False, baseCoin ='USDT'):
        """
        This function takes as predictionsut the json dict with the current wallet state and the new predictions (see elsewhere for more
        info), a p list of percentages that we are alloting to each position (with no constraints on length or order) and prices,
        a pandas Series object with the current BTC (or any other reference coin) value of all the coins we might want to buy or
        sell (if there are coins we are not doing anything with it's not a problem).

        It returns a dataframe with amounts of coins we need to buy, sell and the amount of each.

        NOTE: when a coin is repeated and changes position we ignore the next one (i.e., we only buy two coins)
        TODO: think about this
        """

        p = self.environmentConfigurations.tradingQuantityOfInvestmentInPercentage
        slippageSecurityMarginInPercentage = self.environmentConfigurations.slippageSecurityMarginInPercentage  # amount we want to reserve in TUSD in order to trade
        minimum_amount = self.environmentConfigurations.minimAmountToTradeInDollars  # lower limit to the above amount
        fallbackCoins = self.environmentConfigurations.fallbackCoins

        check = False

        prices = pd.Series(pricePerCoin)

        # Merge and name stuff:
        invests = pd.Series([b['quantity'] for (a, b) in wallet_state['actual_investments'].items()],
                            index=wallet_state['actual_investments'].keys())

        df = pd.concat([invests, prices], axis=1, sort=False).fillna(0)
        df.columns = ['quantity', 'prices']

        if self.environmentConfigurations.currentlyRunningMethodology == "real_money":
            df, max_coin, check = self.minimum_amount_check(df, slippageSecurityMarginInPercentage, minimum_amount, check, baseCoin)
        else:
            max_coin = None

        # Compute the BTC value of each of the coinsp
        df['btc_val'] = df['quantity'].multiply(df['prices'])

        # Compute percentages depending on the amount of coins we want to buy
        len_preds = len(wallet_state['new_predictions'])
        new_percentages = [a / sum(p[:len_preds]) for a in p[:len_preds]]
        new_preds = pd.DataFrame(data={'new_percentages': new_percentages}, index=wallet_state['new_predictions'])

        # Compute new values of each coin we want, in btc and own currency value
        new_preds['new_preds_btc'] = new_preds * df['btc_val'].sum()

        df = pd.concat([df, new_preds], axis=1, sort=False).fillna(0)
        df['new_preds'] = df['new_preds_btc'].div(df['prices'])

        # Compute the differences between before and after; to prevent selling and buying the same coin
        df['dif'] = df['new_preds'] - df['quantity']
        df['sell'] = df['dif'][df['dif'] < -1e-8]
        df['buy'] = df['dif'][df['dif'] > 1e-8]

        # Here we hardcode the event of having to get rid of BTC since "selling" BTC is
        # not contemplated by the tracker -> this needs to be solved in another way
        # Same with buying
        # FIXME: A better way would be to do it in the final trading dict

        """"
        if not np.isnan(df.loc['BTC', 'sell']) or not np.isnan(df.loc['BTC', 'buy']):
            df.loc['BTC', 'sell'] = np.nan
            df.loc['BTC', 'buy'] = np.nan
            df.loc['BTC', 'btc_val'] = 0
            df.loc['BTC', 'quantity'] = 0
            df.loc['BTC', 'new_preds_btc'] = 0
            df.loc['BTC', 'new_preds'] = 0

            self.slack.send("Debugging: we tried to sell BTC but coerced it into removing it from the order")
        """

        # EXCEPTION MADE ONLY FOR TUSD
        # EXCEPTION MADE ONLY FOR TUSD
        # EXCEPTION MADE ONLY FOR TUSD

        if revertMarket:
            df = self.revert_tusd_market_if_exists(df)
        # EXCEPTION MADE ONLY FOR TUSD
        # EXCEPTION MADE ONLY FOR TUSD
        # EXCEPTION MADE ONLY FOR TUSD

        df = self.round_numbers(df)

        repeated = set(wallet_state['actual_investments'].keys()).intersection(list(wallet_state['new_predictions']))

        accountsContainer.addResult(accountName, 'AIpredictions', wallet_state['new_predictions'])
        accountsContainer.addResult(accountName, 'repeated', repeated)
        accountsContainer.addResult(accountName, 'previousCoinsWithMoney', self.coinsWithMoney)

        predictedCoinsWithCurrentCoinValue = {}
        for index, row in enumerate(wallet_state['new_predictions']):
            if row in fallbackCoins:
                row = baseCoin

            predictedCoinsWithCurrentCoinValue[row] = pricePerCoin[row]

        accountsContainer.addResult(accountName, 'predictedCoinsWithCurrentCoinValue', predictedCoinsWithCurrentCoinValue)

        trading_dict = self.create_trading_dict(wallet_state, df, exchange_markets, max_coin, check, minimum_amount, baseCoin, accountName, accountsContainer)
        # This is sent to Process Manager, line 116

        # We reorder the dict to acount for the TUSD exception. That is, we need to sell BTC the last (because
        # it's actually buying TUSD, so there needs to be money) and buy TUSD the first (because it's actually
        # selling TUSD, so there needs to be money)

        ordered_dict = self.define_multi_market_trading_dictionary(trading_dict, accountName, predictions, fallbackCoins)

        return ordered_dict

    def revert_tusd_market_if_exists(self, df):
        # We can't sell or buy TUSD because of the market restrictions, so we need to change the orders
        # to buy or sell BTC instead. We do this in this function

        # For the selling part:
        if not np.isnan(df.loc['TUSD', 'sell']):
            # Retrieve the amount in BTC:
            amount_btc = abs(df.loc['TUSD', 'new_preds_btc'] - df.loc['TUSD', 'btc_val'])

            # Remove the TUSD sell order:
            df.loc['TUSD', 'sell'] = np.nan
            # Remove the amount of TUSD we have (since we "sold")
            #df.loc['TUSD', df.columns[[0, 2, 3, 4, 5]]] = 0
            # Same with BTC, otherwise we'll be buying twice:
            #df.loc['BTC', df.columns[[0, 2, 3, 4, 5]]] = 0
            # Create the buy order:
            df.loc['BTC', 'buy'] = amount_btc

        # Same for the buying part:
        if not np.isnan(df.loc['TUSD', 'buy']):
            # Retrieve the amount in BTC:
            amount_btc = abs(df.loc['TUSD', 'new_preds_btc'] - df.loc['TUSD', 'btc_val'])
            # Remove the TUSD buy order:
            df.loc['TUSD', 'buy'] = np.nan
            # Create the buy order:
            df.loc['BTC', 'sell'] = -amount_btc

        return df

    def create_trading_dict(self, predictions, df, exchange_markets, max_coin, check, amount, baseCoin, accountName, accountsContainer):

        exchange_markets_list = list(exchange_markets.keys())
        """
        This function takes the dataframe from the create_trading_df function and transforms it into a dictionary that can be
        directly exported in json.
        """

        fallbackCoins = self.environmentConfigurations.fallbackCoins

        # Initialize dicts
        df['coin'] = df.index

        dbuy = dict.fromkeys([b['coin'] for a, b in df.iterrows() if b['buy'] > 0])
        dsell = dict.fromkeys([b['coin'] for a, b in df.iterrows() if b['sell'] < 0])

        accountsContainer.addResult(accountName, 'wouldBuy', list(dbuy.keys()))
        accountsContainer.addResult(accountName, 'wouldSell', list(dsell.keys()))

        d = {'buy': dbuy, 'sell': dsell,
             'repeated': set(predictions['actual_investments'].keys()).intersection(list(predictions['new_predictions']))}

        # Fill dicts with appropriate data
        for index, row in df.iterrows():

            if row['coin'] not in exchange_markets_list:
                continue

            base_market = row['coin']

            if base_market in fallbackCoins:
                base_market = baseCoin

            if row['buy'] > 0:
                d['buy'][base_market] = {'quantity': row['buy'], 'market': exchange_markets[ base_market ]['market'] }
            elif row['sell'] < 0:
                d['sell'][base_market] = {'quantity': abs(row['sell']), 'market': exchange_markets[ base_market ]['market'], 'btc_amount': row['btc_val'] }

        if check:
            self.slack.send("I have sold " + str(amount) + " in " + max_coin + " for the BTC buffer.")
            if max_coin in d['sell']:
                d['sell'][max_coin]['quantity'] += amount
            else:
                # d['sell'].append({max_coin: {'quantity':amount, 'market': exchange_markets[max_coin]['market']}})
                d['sell'][max_coin] = {'quantity': amount, 'market': exchange_markets[max_coin]['market'], 'btc_amount': df.loc[max_coin, 'btc_val']}

        d = {accountName: d}

        return d

    def define_multi_market_trading_dictionary(self, trading_dict, accountName, predictions, fallbackCoins):
        # In this function we just reorder the dict to sell BTC last (as this is actually buying TUSD) and to
        # buy btc first, since this is selling TUSD
        ordered_dict = {}

        predictedCoin = predictions[0]

        for key, element in trading_dict.items():
            ordered_dict[key] = {'1': {'sell': {}},
                                 '2': {'buy': {}},
                                 '3': {'sell': {}},
                                 '4': {'buy': {}},
                                 'repeated': []}
            # Selling
            check = False
            for coin in element['sell']:
                # if coin != 'BTC':
                    ordered_dict[key]['1']['sell'].update({coin: trading_dict[key]['sell'][coin]})
                # else:
                #     check = True
                # We put the TUSD last (since we are actually buying and we need money)

            if check and predictedCoin not in fallbackCoins:
                ordered_dict[key]['3']['sell'].update({predictedCoin: trading_dict[key]['sell'][predictedCoin]})
            # Buying
            # We put the BTC first, since we are be selling TUSD

            # TODO Wtf are those hardcoded coins, deprecate please
            if predictedCoin in trading_dict[accountName]['buy'].keys() and predictedCoin not in fallbackCoins:
                ordered_dict[key]['2']['buy'].update({predictedCoin: trading_dict[key]['buy'][predictedCoin]})

            for coin in element['buy']:
                if coin != 'BTC' and coin != 'ETH':
                    ordered_dict[key]['4']['buy'].update({coin: trading_dict[key]['buy'][coin]})
                else:
                    pass

            # We need to also add the "repetead" field
            ordered_dict[key]['repeated'] = trading_dict[key]['repeated']
        return ordered_dict

    # TODO add BTC min amount too
    def minimum_amount_check(self, df, splippageSecurityMargin, minimum, check=False, baseCoin='USDT'):

        # TODO the slippage calculation has to be done on buy operations only
        # THIS IS NOT IN USE ANYMORE, I LEAVE IT FOR FUTURE REFACTORING
        # if baseCoin == 'BTC':
        #
        #     if df.loc['TUSD', 'quantity'] > splippageSecurityMargin:
        #         # If there are more than minimum TUSD we just use those as buffer, and we are done
        #         df.loc['TUSD', 'quantity'] -= splippageSecurityMargin
        # if baseCoin == 'USDT':
        #     if df.loc['USDT', 'quantity'] > splippageSecurityMargin:
        #         df.loc['USDT', 'quantity'] -= splippageSecurityMargin

        max_coin = None

        # TODO what the fuck is max_coin and check
        return self.round_numbers(df), max_coin, check

    @staticmethod
    def round_numbers(df):
        return df.apply(lambda x: round(pd.to_numeric(x), 8), axis=1)

