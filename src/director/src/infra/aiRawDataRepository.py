from src.domain.aiRawData import AiRawData

class AiRawDataRepository:

    def __init__(
        self,
        environmentConfigurations,
        Database
    ):
        self.Database = Database
        self.environmentConfigurations = environmentConfigurations
        self.raw_data_collection = self.Database.ai_environment
        self.indicators_collection = self.Database.raw_data_and_indicators

    def save(self, results: AiRawData) -> None:
        if self.environmentConfigurations.ai_db_enabled == True:
            self.raw_data_collection.insert(results.toObject(), check_keys=False)

    def saveManyIndicators(self, results: AiRawData) -> None:
        if self.environmentConfigurations.ai_db_enabled == True:
            self.indicators_collection.insert_many(results.getIndicators())
