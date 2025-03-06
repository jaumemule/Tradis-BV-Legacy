import unittest
import sys
import os

from src.application.SlackClient import Slack
from src.application.environmentConfigurations import EnvironmentConfigurations
from src.infra.Database import Database
from src.infra.TrackerRepository import TrackerRepository
from src.infra.BalancesRepository import BalancesRepository
from src.infra.ApiClient import ApiClient
from src.domain.CouldNotRetrieveTrackerDataException import CouldNotRetrieveTrackerDataException

sys.path.append('/usr/app/src/tracker')

from src.application.environmentConfigurations import EnvironmentConfigurations
from src.domain.StopLoss import StopLoss

class TestSandboxConfigurationsAreSet(unittest.TestCase):

    def stubs(self):
        env = EnvironmentConfigurations()
        return StopLoss(
            env,
            BalancesRepository(EnvironmentConfigurations, Database(env)),
            Slack(env.slackToken, env.environmentName),
            ApiClient(env)
        )

    def test_stop_trading_if_percentage_of_loss_is_superior_or_equal(self):

        stop_loss = self.stubs()
        self.assertEqual(stop_loss.shouldStopTrading(0.5, 0.6), True)
        self.assertEqual(stop_loss.shouldStopTrading(0.6, 0.6), True)

    def test_do_not_stop_trading_if_percentage_of_loss_is_inferior(self):

        stop_loss = self.stubs()
        self.assertEqual(stop_loss.shouldStopTrading(0.7, 0.6), False)

    def test_calculate_percentage_of_loss(self):
        stop_loss = self.stubs()
        self.assertEqual(stop_loss.calculatePercentageOfLoss(10, 20), 100)
        self.assertEqual(stop_loss.calculatePercentageOfLoss(1, 1.5), 50)

    def test_percentage_of_loss_should_be_zero_if_we_win(self):
        stop_loss = self.stubs()
        self.assertEqual(stop_loss.calculatePercentageOfLoss(1000, 5), 0)

    def test_should_unlock_coin(self):

        stop_loss = self.stubs()

        shouldUnlock, percentage = stop_loss.shouldUnlockCoins(10, 5)
        self.assertEqual(shouldUnlock, True)
        self.assertEqual(percentage, 100)

    def test_should_not_unlock_coin(self):

        stop_loss = self.stubs()
        shouldUnlock, percentage = stop_loss.shouldUnlockCoins(4, 5)
        self.assertEqual(shouldUnlock, False)
        self.assertEqual(percentage, 0)

