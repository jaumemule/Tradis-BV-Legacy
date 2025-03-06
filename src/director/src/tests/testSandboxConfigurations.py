import unittest
import sys
import os

sys.path.append('/usr/app/src/director')

from src.infra.environmentConfigurations import EnvironmentConfigurations

class TestSandboxConfigurationsAreSet(unittest.TestCase):

    def test_configurations_contains_wallet_url_set_and_poiting_to_staging_when_no_environment_is_set(self):
        os.environ['ENVIRONMENT'] = ''
        configurations = EnvironmentConfigurations()

        self.assertEqual(configurations.walletUrl, 'http://ns3089372.ip-178-32-220.eu:3000/api/v1')

    def test_configurations_contains_staging_api_url_set_and_poiting_docker_network_if_no_dev_env_set_but_docker(self):
        os.environ['ENVIRONMENT'] = 'dev'
        configurations = EnvironmentConfigurations()

        self.assertEqual(configurations.walletUrl, 'http://ns3089372.ip-178-32-220.eu:3000/api/v1')

    def test_configurations_contains_staging_api_url_set_and_poiting_docker_network_if_env_set(self):
        os.environ['WALLET_URL'] = 'http://ns3089372.ip-178-32-220.eu:3000/api/v1'
        os.environ['ENVIRONMENT'] = 'dev'
        configurations = EnvironmentConfigurations()

        self.assertEqual(configurations.walletUrl, 'http://ns3089372.ip-178-32-220.eu:3000/api/v1')
    def test_configurations_contains_wallet_url_set_and_poiting_local_network_if_dev_production(self):
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['WALLET_URL'] = 'http://localhost:3000/api/v1'
        configurations = EnvironmentConfigurations()

        self.assertEqual(configurations.walletUrl, 'http://localhost:3000/api/v1')
