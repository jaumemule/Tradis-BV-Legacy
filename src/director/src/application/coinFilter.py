import pandas as pd
import os

class CoinFilter:

    def filterFromFileToTable(self, fileToLoadInCsv: str, tableToFilter) -> list:
        filtered_coins = pd.read_csv(fileToLoadInCsv + '.csv', index_col=0)
        filtered_coins = list(filtered_coins.index)
        filtered = tableToFilter[tableToFilter.index.isin(filtered_coins)]

        return filtered

    def filterFromFileToTable2(self, fileToLoadInCsv: str, tableToFilter) -> list:
        with open(os.path.join('src', 'infra', fileToLoadInCsv + '.csv')) as f:
            filtered_coins = f.readlines()
        filtered_coins = [x.strip() for x in filtered_coins]
        temp_coins = [a for a in list(tableToFilter.index) if a.split('.')[0] in filtered_coins]
        filtered = tableToFilter[tableToFilter.index.isin(temp_coins)]

        return filtered
