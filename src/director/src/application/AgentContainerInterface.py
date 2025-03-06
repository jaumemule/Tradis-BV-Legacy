from abc import ABC, abstractmethod
from src.infra.balancesRepository import BalancesRepository
import datetime

class AgentContainerInterface(ABC):

    @abstractmethod
    def load_model_configurations(self): raise NotImplementedError

    @abstractmethod
    def create_agent(self, agent_filename): raise NotImplementedError

    @abstractmethod
    def predict(self, mode: str, atDateTime: datetime.datetime, storeQValues: bool, storeObservations: bool) -> list: raise NotImplementedError

    @abstractmethod
    def previous_coin_hold(self) -> list: raise NotImplementedError

    @abstractmethod
    def ML_signal(self) -> list: raise NotImplementedError
