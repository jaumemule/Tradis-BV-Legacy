from src.domain.Simulation import Simulation

class SimulationResultsRepository:

    def __init__(
        self,
        environmentConfigurations,
        Database
    ):
        self.Database = Database
        self.environmentConfigurations = environmentConfigurations
        self.simulations_aggregation = self.Database.simulations_aggregation

    def aggregateByDateRange(self, results: Simulation) -> None:
        self.Database.simulations_aggregation.insert_one(results.toObject())
