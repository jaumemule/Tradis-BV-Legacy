from bson.objectid import ObjectId

class BalanceStateObject(object):

    __create_key = object()

    def __init__(self, create_key, balances: dict, rates: dict, totals: dict, userId: ObjectId, strategyId: ObjectId):

        assert(create_key == BalanceStateObject.__create_key), \
            "BalanceStateObject objects must be created using BalanceStateObject named constructor method from_exchange_rate_and_balance"

        self.balances = balances
        self.rates = rates
        self.totals = totals
        self.userId = userId
        self.strategyId = strategyId

    @classmethod
    def from_exchange_rate_and_balance(
            self,
            exchange_rates: dict,
            balances: dict,
            strategy: dict,
            account: dict
    ):
        # 1. Convert all the coins in base coin(coinsToComputeWithoutBaseCoinList): loop(balance of coin * exchange rate price ), then + base coin amount total_in_base_coin = 0
        total_in_base_coin = 0
        base_coin = strategy['baseCoin']
        coins_to_compute_from_strategy = list(strategy['exchangeMarkets'].keys())

        coins_to_compute_from_strategy_without_base_coin = coins_to_compute_from_strategy.copy()
        coins_to_compute_from_strategy_without_base_coin.remove(base_coin)

        for coin in balances:
            if base_coin != coin and coin in coins_to_compute_from_strategy_without_base_coin:
                # 2. Sum all the conversions to get the base coin amount
                conversion = balances[coin] * exchange_rates[coin]['p']
                total_in_base_coin += conversion

        if base_coin in balances: # TODO check if this is a bug
            total_in_base_coin += balances[base_coin]
        else:
            print('---- no balance found for ', str(account), str(balances))

        # 3. Now, use the result of point 2 and use exchange rate to convert to the desired coin: balance in base coin / exchange rate price
        total_balance_in_every_coin_dict = {}

        for coin in coins_to_compute_from_strategy_without_base_coin:
            total_in_base_coin_from_base_coin = total_in_base_coin / exchange_rates[coin]['p']
            total_balance_in_every_coin_dict[coin] = round(total_in_base_coin_from_base_coin, 8)

        total_balance_in_every_coin_dict[base_coin] = total_in_base_coin # do not forget to add base coin

        if '_user' in account:
            user = ObjectId(account['_user'])
        else:
            print('User not found for account', account)
            user = None

        # TODO delete coins not in use for strategy in balance. we output all of them right now, increasing storage for no reason
        return BalanceStateObject(
            self.__create_key,
            balances,
            exchange_rates,
            total_balance_in_every_coin_dict,
            user,
            ObjectId(strategy['_id']),
        )

    def get_balances(self) -> dict:

        return self.balances

    def get_rates(self) -> dict:

        return self.rates

    def get_totals(self) -> dict:

        return self.totals

    def get_user_id(self) -> ObjectId:

        return self.userId

    def get_strategy_id(self) -> ObjectId:

        return self.strategyId
