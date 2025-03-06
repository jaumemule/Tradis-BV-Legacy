import pandas as pd
import json

class FileLoader:
    def loadCsvWithIndexColZeroMode(filePath) -> object:
        return pd.read_csv(filePath, index_col=0)

    def loadJson(filePath) -> list:
        with open(filePath) as f:
            return json.load(f)