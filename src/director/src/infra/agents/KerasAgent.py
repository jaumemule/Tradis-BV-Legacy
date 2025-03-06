from src.application.AgentContainerInterface import AgentContainerInterface
from src.infra.balancesRepository import BalancesRepository
from src.infra.aiRawDataRepository import AiRawDataRepository
from src.application.dataProvider import DataProvider
import os
import gym
from gym.envs.registration import register, make
import datetime
from rl_fork.agents.dqn import DQNAgent
from src.infra.binanceCreateModel import create_model
from rl_fork.policy import EpsGreedyQPolicy, GreedyQPolicy
from rl_fork.memory import SequentialMemory
from rl_fork.core import Processor
from keras.optimizers import Adam
from pandas.io.json import json_normalize
import json
from src.domain.aiRawData import AiRawData

class KerasAgent(AgentContainerInterface):
    agent = None
    env = None
    modelTimestamp = None
    indices_list = ["p", "o", "l", "h"]

    def __init__(
        self,
        BalancesRepository: BalancesRepository,
        AiRawDataRepository: AiRawDataRepository,
        strategy,
        slackClient,
        isSimulation,
    ):
        self.ai_raw_data_repository = AiRawDataRepository
        self.slackClient = slackClient
        self.strategy = strategy
        self.isSimulation = isSimulation
        self.out_list = 6
        self.indicator_periods = 25
        self.BalancesRepository = BalancesRepository
        cfg = strategy['mlEnvConfigs']
        self.data_window = 1  # TODO create a config file
        self.max_episode_timesteps = cfg["training"]["max_episode_timesteps"]
        self.forecast_len = cfg["about_data"]["forecast_len"]
        self.candle_size = cfg["about_data"]["candle_size"]
        self.reference_coin = cfg["financial"]["reference_coin"]

        # we understand the first one as the base coin
        self.coins = ["USDT", "BTC"]

        # To keep track of the last action
        self.last_coin_index = 1  # position: 0 - USDT, 1 - BTC

    def load_model_configurations(self):

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
        # model = ModelWrapper(env).build_model_(which='original')  # Do not remove; might be used in the near future
        self.env.input_shape = (
            1,
            self.indicator_periods + self.out_list,
        )  # number of features

        self.model = create_model(self.env)
        self.memory = SequentialMemory(
            limit=5000, window_length=1
        )  # TODO: remove hardcoded values
        self.policy = EpsGreedyQPolicy()
        self.test_policy = GreedyQPolicy()

    def create_agent(self, agent_filename):
        self.agent = DQNAgent(
            processor=Processor(),
            model=self.model,
            nb_actions=self.env.action_size,
            memory=self.memory,
            nb_steps_warmup=50,
            target_model_update=1e-2,
            policy=self.policy,
        )
        self.agent.compile(Adam(lr=1e-3), metrics=["mse"])

        directory = os.path.join(os.getcwd(), "saves", "agent")
        filestar = os.path.join(directory, agent_filename)
        self.agent.load_weights(filestar)

    def _retrieve_data(self, atDateTime):
        # do not need reference coin
        coins = [a for a in self.coins if a != self.reference_coin]

        # Initialize data class (but don't load data yet)
        dataProvider = DataProvider(
            self.BalancesRepository,
            coin_list=coins,
            indices_list=self.indices_list,
            runAt=atDateTime,
            slackClient=self.slackClient,
            mlEnvConfigs=self.strategy['mlEnvConfigs']
        )

        reverse = False
        if 'predictForTargetCoin' in self.strategy['mlEnvConfigs']:
            reverse = self.strategy['mlEnvConfigs']['predictForTargetCoin']

        df = dataProvider.retrieve_data(
            time_frame=self.data_window,
            candle_size=self.candle_size,
            base_coin=self.strategy["baseCoin"],
            reverse=reverse
        )
        df = dataProvider.to_float(df)
        df = dataProvider.compute_all_indicators(df)

        store_df = df.copy().transpose()
        store_df['date'] = store_df.index
        store_df.index = store_df.index.astype(str)
        store_df.columns = [a.replace(".", "_") for a in store_df.columns]
        store_df['strategy_id'] = self.strategy['_id']

        self.ai_raw_data.addIndicators(store_df.to_dict(orient='records'), self.strategy['mlEnvConfigs']['about_data']['candle_size'])

        try:
            self.ai_raw_data_repository.saveManyIndicators(self.ai_raw_data)
        except Exception:
            self.slackClient.send('Could not store indicators for Procyon')

        df = dataProvider.analyzer.analyze_non_reals(df)

        # Import the actions from the repo
        actions, actions_dict, isMock = self._retrieve_actions(atDateTime)

        actions.drop("_id", inplace=True, axis=1)
        actions.set_index("date", drop=True, inplace=True)

        # Reshuffle the dataframe and add the actions
        df = dataProvider.data_shape_correction(df).transpose()
        df = df.merge(actions, left_index=True, right_index=True)
        df = df.drop_duplicates()

        column_names = [
            dataProvider.coin_list[0] + "." + a
            for a in dataProvider.get_feature_names()
        ]
        column_names += ["action"]
        df = df[column_names]

        return dataProvider.to_float(df)

    def _retrieve_actions(self, atDateTime):

        window = 10  # give me last 10 fallback hours and pick 1 later
        beginning = atDateTime - datetime.timedelta(minutes=window * self.candle_size)
        data = self.BalancesRepository.retrieveActions(beginning, atDateTime)

        mock = False
        if len(data) == 0:
            mock = True
            print("created a mock data action")
            lastAction = [
                {"_id": 1, "date": atDateTime, "action": 1, "coin": 1},
            ]
        else:
            lastAction = [data[len(data) - 1]]  # pick last one
            lastAction[0][
                "date"
            ] = atDateTime  # to prevent +1 minute in some accounts if happens, or if 1h is missing

        return json_normalize(lastAction), lastAction[0], mock

    def _insert_action(self, signal_id, coin_index, atDateTime, isMock) -> dict:
        str_time = atDateTime.strftime(
            "%d/%m/%Y %H:%M:%S"
        )  # TODO: There must be a way to transform directly
        date = datetime.datetime.strptime(str_time, "%d/%m/%Y %H:%M:%S")

        # this is not necessary anymore, since we replace the date on retrieve
        # date += datetime.timedelta(minutes=+self.candle_size)

        # IMPORTANT NOTE:
        # yeah, the opposite in purpose. action is required by the ML and refers to the
        # coin we are: coin_index (USDT/BTC) and action_from_ml is just information for
        # us, the output from ML (0 (sell) ,1 (hold) , 2 (buy))

        state = {
            "date": date,
            "action": int(signal_id),
            "coin": int(coin_index),
            "is_mock": isMock,
        }

        self.BalancesRepository.recordActions(
            state
        )

        return state

    def predict(
        self, mode: str, atDateTime, storeQValues=False, storeObservations=False
    ) -> list:

        self.ai_raw_data = AiRawData(self.strategy['_id'])
        self.ai_raw_data.setDate(atDateTime)
        self.ai_raw_data.setCandles([self.strategy['mlEnvConfigs']['about_data']['candle_size']])

        # Create observation
        observation = self._retrieve_data(atDateTime)

        stored_observation = observation.copy()

        stored_observation.columns = [
            a.replace(".", "_") for a in stored_observation.columns
        ]
        stored_observation = json.loads(stored_observation.T.to_json()).values()

        if storeObservations:
            self.ai_raw_data.setObservations(list(stored_observation)[0])

        self.previous_action = None
        self.current_signal = None

        previous_state, previous_state_dict, isMock = self._retrieve_actions(atDateTime)

        self.previous_action = previous_state_dict

        # VITAL ALERT: enable only in local since we modify a vendor dependency
        # if fails, return q_values from the forward method
        if storeQValues == True:
            signal, qvalues = self.agent.forward(
                observation.values[-self.data_window:, :]
            )

            qvalues = [float(a) for a in qvalues]

            stored_qvalues = {
                "sell": qvalues[0],
                "hold": qvalues[1],
                "buy": qvalues[2],
            }

            self.ai_raw_data.setQvalues(stored_qvalues)
        else:
            # Predict action
            signal = self.agent.forward(observation.values[-self.data_window :, :])

        signal_id = signal  # can come as tupple or int (yes, what the fff...)

        if type(signal) is tuple:
            signal_id = signal[0]  # taken from tupple

        self.current_signal = signal_id

        coin_index = self.signal_to_coin(signal_id)

        # hold means we stay in the previous coin
        # print('coin index: ', coin_index, 'signal: ', signal, 'signal ID: ',  signal_id)
        # print('previous state', previous_state_dict)
        if coin_index == None:
            state = self._insert_action(
                signal_id, int(previous_state_dict["coin"]), atDateTime, isMock
            )

            self.ai_raw_data.setState(state)

            coin_index = previous_state_dict["coin"]
        else:
            state = self._insert_action(signal_id, coin_index, atDateTime, isMock)
            self.ai_raw_data.setState(state)

        if storeQValues == True or storeObservations == True:
            try:
                self.ai_raw_data_repository.save(self.ai_raw_data)
            except Exception:
                self.slackClient.send('Could not store qvalues and observations for Procyon')

        # Return predicted coin if any
        return [self.coins[coin_index]]  # the strategy has only 1 coin prediction

    def previous_coin_hold(self):
        return [
            self.coins[int(self.previous_action["coin"])]
        ]  # the strategy has only 1 coin prediction

    def ML_signal(self):
        return [self.current_signal]  # the strategy has only 1 coin prediction

    def signal_to_coin(self, signal_id):

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
