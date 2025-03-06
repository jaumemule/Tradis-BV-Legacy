from src.application.AgentContainerInterface import AgentContainerInterface
from src.domain.tradingIndicators import TradingIndicators
from src.infra.agents.agentWrapper import AgentWrapper
from src.infra.balancesRepository import BalancesRepository
from src.infra.aiRawDataRepository import AiRawDataRepository
from src.application.generalizedDataProvider import GeneralizedDataProvider
import os
import gym
import numpy as np
from gym.envs.registration import register, make
import datetime
from rl_fork.policy import EpsGreedyQPolicy, GreedyQPolicy
from rl_fork.custom_memory import PosNegSequentialMemory
from pandas.io.json import json_normalize
import json
from src.infra.modelWrapper import ModelWrapper

class KerasAgent2(AgentContainerInterface):
    agent = None
    env = None
    modelTimestamp = None
    indices_list = ["p", "o", "l", "h", "v"]
    current_signal = None

    def __init__(
            self,
            BalancesRepository: BalancesRepository,
            AiRawDataRepository: AiRawDataRepository,
            strategy,
            slackClient,
            isSimulation,
    ):
        self.AiRawDataRepository = AiRawDataRepository
        self.slackClient = slackClient
        self.strategy = strategy
        self.isSimulation = isSimulation
        self.BalancesRepository = BalancesRepository

        # To keep track of the last action
        # AI simulations start in USDT; TODO: review (jaume)
        self.last_coin_index = 1  # position: 0 - USDT, 1 - BTC

    def load_model_configurations(self):

        self.cfg = self.strategy['mlEnvConfigs']

        self.coins = [self.cfg['financial']['reference_coin'], self.cfg['financial']['trading_coin']]

        self.data_window = self.cfg["about_data"]["window"]
        self.history_units = self.cfg["network"]["history_units"]
        self.max_episode_timesteps = self.cfg["training"]["max_episode_timesteps"]
        self.forecast_len = self.cfg["about_data"]["forecast_len"]
        self.candles = self.cfg["about_data"]["candles"]
        self.reference_coin = self.cfg["financial"]["reference_coin"]
        self.model_name = self.cfg["agent"]["model_type"]
        self.indicator_num = TradingIndicators(self.cfg).get_indicator_number()

        self.parameters = {
            "alpha": self.cfg["agent"]["alpha"],
            "batch_size": self.cfg["agent"]["batch_size"],
            "candles": self.candles,
            "dense_units": self.cfg["agent"]["dense_units"],
            "dropout": self.cfg["agent"]["dropout"],
            "inner_units": self.cfg["agent"]["inner_units"],
            "proba": self.cfg["agent"]["proba"],
            "threshold": self.cfg["agent"]["threshold"],
            "lr": self.cfg["agent"]["lr"],
            "agent_type": self.cfg["agent"]["agent_type"]
        }

        if 'korybas' in self.strategy['strategyName']:
            self.parameters['l1'] = self.cfg["network"]["l1"]
            self.parameters['l2'] = self.cfg["network"]["l2"]


        # Initialize environment
        ENV_NAME = "kerasEnvironment-v0"

        if ENV_NAME in gym.envs.registry.env_specs:
            del gym.envs.registry.env_specs[ENV_NAME]

        register(
            id=ENV_NAME,
            entry_point="src.infra.envs:KerasEnvironment",
            max_episode_steps=10000,
        )

        self.env = make(ENV_NAME)

        # Load model and policy
        self.env.input_shape = (self.data_window, len(self.candles), self.indicator_num)
        self.env.history_shape = (1, self.history_units)

        self.model = ModelWrapper(self.env, cfg=self.cfg).build_model(which=self.model_name,
                                                        parameters=self.parameters)
        self.memory = PosNegSequentialMemory(limit=10000, window_length=1,
                                             pos_proba=self.parameters["proba"],
                                             threshold=self.parameters["threshold"]
                                             )
        self.policy = EpsGreedyQPolicy()
        self.test_policy = GreedyQPolicy()

    def create_agent(self, agent_filename):
        self.agent = AgentWrapper(self.env, which=self.parameters["agent_type"])
        self.agent.create(model=self.model,
                          memory=self.memory,
                          warmup_steps=50,
                          policy=self.policy,
                          test_policy=self.test_policy,
                          train_interval=1,
                          batch_size=self.parameters["batch_size"])

        self.agent.compile(lr=self.parameters["lr"])

        directory = os.path.join(os.getcwd(), "saves", "agent")
        filestar = os.path.join(directory, agent_filename)
        self.agent.load_weights(filestar)

    def _retrieve_data(self, atDateTime):
        # do not need reference coin
        coins = [a for a in self.coins if a != self.reference_coin]

        # Initialize data class (but don't load data yet)
        dataProvider = GeneralizedDataProvider(
            self.BalancesRepository,
            coin_list=coins,
            indices_list=self.indices_list,
            runAt=atDateTime,
            slackClient=self.slackClient,
            cfg=self.cfg
        )

        reverse = False
        if 'predictForTargetCoin' in self.cfg:
            reverse = True

        df = dataProvider.retrieve_data(
            candles=self.candles,
            forecast_len=self.forecast_len,
            time_frame=self.data_window,
            base_coin=self.strategy["baseCoin"],
            reverse=reverse
        )

        df = dataProvider.to_float(df)
        df = dataProvider.rolling_normalization(df)
        df = dataProvider.analyzer.analyze_non_reals(df)
        # FIXME: probably not needed anymore (eudald)
        df = dataProvider.data_shape_correction(df)

        return df

    def _retrieve_actions(self, atDateTime):

        window = 10  # give me last 10 fallback hours and pick 1 later
        beginning = atDateTime - datetime.timedelta(minutes=window * max(self.candles))
        data = self.BalancesRepository.retrieveActions(beginning, atDateTime)

        if len(data) == 0:
            print("created a mock data action")
            last = [{"action": 1, "coin": 1, "gain": 0}]
            return json_normalize(last), None, True

        else:
            last = json_normalize(data)
            # In the second pass we still can't compute the gain, so we must put it by
            # hand
            last["gain"] = 0 if len(data) == 1 else last["current_price"].pct_change()
            cols_ = ["action", "coin", "gain"]

            return last[cols_].iloc[-1:, ], last["current_price"].iloc[-1], False

    def _insert_action(self, signal_id, coin_index, atDateTime, current_price, isMock):

        # IMPORTANT NOTE:
        # FIXME: this is not true, right? Remove comment? (jaume)
        # yeah, the opposite in purpose. action is required by the ML and refers to the
        # coin we are: coin_index (USDT/BTC) and action_from_ml is just information for
        # us, the output from ML (0 (sell) ,1 (hold) , 2 (buy))
        self.BalancesRepository.recordActions(
            {
                "date": atDateTime,
                "action": int(signal_id),
                "coin": int(coin_index),
                "current_price": current_price,
                "is_mock": isMock,
            }
        )

    def _store_observation(self, observation, atDateTime):
        stored_observation = observation.copy()
        stored_observation.columns = [
            a.replace(".", "_") for a in stored_observation.columns
        ]
        stored_observation["date"] = str(atDateTime)
        stored_observation = json.loads(stored_observation.T.to_json()).values()

        self.BalancesRepository.recordAIObservations(stored_observation)

    def _store_qvalues(self, qvalues, atDateTime):
        qvalues = [float(a) for a in qvalues]
        stored_qvalues = {
            "sell": qvalues[0],
            "hold": qvalues[1],
            "buy": qvalues[2],
        }
        # self.BalancesRepository.recordAIQvalues(stored_qvalues)

    def _get_last_price(self, atDateTime, last_price):
        data = self.BalancesRepository.retrieve_data_by_one_indicator_and_period_of_time(
            atDateTime + datetime.timedelta(minutes=-20),
            atDateTime,
            f"{self.coins[1]}.p",
            self.coins[0]
        )
        try:
            prices = GeneralizedDataProvider.to_float(json_normalize(data)[f"{self.coins[1]}.p"])
            return prices[~np.isnan(prices)].iloc[-1]
        except KeyError:
            # If we don't find the price, set it to the last one we have
            return last_price

    def predict(self, mode: str, atDateTime, storeQValues=False,
                storeObservations=True) -> list:

        # Create observation
        observation = self._retrieve_data(atDateTime)

        if storeObservations:
            self._store_observation(observation, atDateTime)

        previous_info, last_price, isMock = self._retrieve_actions(atDateTime)
        # Why is this called action if it's a coin? FIXME (jaume)
        # There is a parameter in __init__ called last_coin_index that we are not using
        # anywhere, are they the same?
        self.previous_action = previous_info["coin"]

        state = self._construct_state(observation, previous_info)

        # VITAL ALERT: enable only in local since we modify a vendor dependency
        # if fails, return q_values from the forward method
        # UPDATE: it's not a dependency anymore; we always do this now.
        # TODO: remove comment (jaume)

        # Get the action from the AI
        signal, qvalues = self.agent.forward(state)

        if storeQValues:
            self._store_qvalues(qvalues, atDateTime)

        signal_id = signal  # can come as tupple or int (yes, what the fff...)
        # FIXME: this will only come as a tuple in the updated version of the library
        #  where we also return the qvalues - this can be removed (jaume)
        if type(signal) is tuple:
            signal_id = signal[0]  # taken from tupple

        # Store the signal for later
        self.current_signal = signal_id

        # Get coin price
        current_price = self._get_last_price(atDateTime, last_price)

        # Retrieve coin
        current_coin = self._correct_action(signal_id, previous_info["coin"].iloc[0])

        # Insert action
        self._insert_action(signal_id, current_coin, atDateTime, current_price, isMock)

        # Return predicted coin
        return [self.coins[current_coin]]

    def _construct_state(self, input1, input2):
        input1 = input1.values
        dim1_ = int(input1.size / self.data_window / len(self.candles))
        input1 = np.reshape(
            input1, newshape=[dim1_, self.data_window, len(self.candles)]
        )
        # Put window (time variable) first
        input1 = np.swapaxes(input1, 0, 1)
        input1 = np.swapaxes(input1, 1, 2)

        return {"Input_1": input1, "Input_2": input2.values}

    def previous_coin_hold(self):
        return [
            self.coins[int(self.previous_action)]
        ]  # the strategy has only 1 coin prediction

    def ML_signal(self):
        return [self.current_signal]  # the strategy has only 1 coin prediction

    def signal_to_coin(self, signal_id):
        # Obsolete; the new methodology is clearer and matches the AI training one
        # TODO: remove (jaume)

        # if signal_id == 0 will sell (USDT/EUR... -> base coin)
        # if signal_id == 1 will hold (no predictions)
        # if signal_id == 2 will buy (BTC)

        # Sell
        if signal_id == 0:
            coin_index = 0

        # Hold
        elif signal_id == 1:
            coin_index = None

        # Buy
        else:
            coin_index = 1

        # self.last_coin_index = coin_index

        return coin_index

    @staticmethod
    def _correct_action(signal, last_coin):
        # Same name as the env function that does the same
        if signal == 0:
            return 0  # USDT
        elif signal == 1:
            return last_coin
        else:
            return 1  # BTC
