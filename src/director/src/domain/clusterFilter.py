class ClusterFilter:

    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations

    def fromPredictions(self, preds: list, strategy, maximum_coins_to_trade) -> list:

        for coin in self.environmentConfigurations.fallbackCoins:
            if coin in preds:

                # THIS IS TO MAP USDT / EUR / AND SUCH
                preds.remove(coin)
                preds.append(strategy['baseCoin'])

        return preds[:maximum_coins_to_trade]
