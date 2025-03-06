from src.application.AgentContainerInterface import AgentContainerInterface
from src.infra.balancesRepository import BalancesRepository
from src.infra.aiRawDataRepository import AiRawDataRepository
import importlib

class AgentFactory():

    def __init__(self, BalancesRepository: BalancesRepository, AiRawDataRepository: AiRawDataRepository, strategy, slackClient = False):
        self.slackClient = slackClient
        self.strategy = strategy
        self.BalancesRepository = BalancesRepository
        self.AiRawDataRepository = AiRawDataRepository

    def load(self, isSimulation = False) -> AgentContainerInterface:

        agentFileName = self.strategy['agentClassName']
        module = importlib.import_module('src.infra.agents.' + agentFileName)
        AgentEnvironment = getattr(module, agentFileName)

        agent = AgentEnvironment(self.BalancesRepository, self.AiRawDataRepository, self.strategy, self.slackClient, isSimulation)
        agent.load_model_configurations()
        agent.create_agent(agent_filename=self.strategy['modelFileName'])
        return agent
