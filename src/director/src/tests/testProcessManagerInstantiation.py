import unittest
import sys

sys.path.append('/usr/app/src/director')

from src.application.ProcessManager import ProcessManager
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src.infra.database import Database
from src.infra.balancesRepository import BalancesRepository
from src.infra.walletClient import Wallet
from src.infra.ApiClient import ApiClient

class TestSandboxConfigurationsAreSet(unittest.TestCase):

    def test_instantiation_goes_fine(self):
        configurations = EnvironmentConfigurations()
        process = ProcessManager(
            configurations,
            BalancesRepository(
                configurations,
                Database(
                    configurations
                ),
            ),
            Wallet(configurations),
            ApiClient(configurations),
            Database(
                configurations
            )
        )

        assert process is not None
