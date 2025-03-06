import numpy as np
import gym


class KerasEnvironment(gym.Env):

    candles = None
    prices = None
    data_len = None
    window = None
    num_indicators = None
    num_training_episodes = 1

    def __init__(self):
        self.num_extra_inputs = 3  # action, position, gain
        self.actions = [-1, 0, 1]  # sell, sit, buy
        self.action_size = len(self.actions)  # action size
        self.df = None  # data frame which holds data features and close price
        self.initial_account = 100  # dollars
        self.offset = 20  # any episode does not start before the offset
        self.rand_start_index = 0  # random starting index of the episode
        self.pos = 0  # position: 1 - traded, 0 - no trade
        self.account = self.initial_account  # running account
        self.total = 0  # total number of coins
        self.sim_len = 0  # simulation length
        self.t = 0  # time index
        self.gain = 0  # running profit
        self.episode = 0  # episode number
        self.episode_old = 0  # previous episode number
        self.trades = 0  # number of trades
        self.input_shape = None  # input shape for the deep network
        self.current_index = 0  # current time index
        self.is_random = True  # random start
        self.total_steps = 0
        self.col_names = {
            "open": "open",
            "close": "close",
            "high": "high",
            "low": "low",
            "volume": "volume",
        }
        self.fee = 0.001
        self.trade_ratio = 0

    def init_env(self, df, prices, candles, num_episodes=1, window=1, is_random=True):
        self.trades = 0  # number of trades
        self.candles = candles
        self.is_random = is_random
        self.df = df
        self.prices = prices
        self.data_len = self.df.shape[0]
        self.sim_len = self.data_len
        self.window = window
        self.num_indicators = int(self.df.shape[1] / len(candles))

        # IMPORTANT: the first shape is of the main NN, first goes the window (the time
        # dimension), then the number of candles and finally the number of indicators
        # per candle. The second shape is the one of the "historical" or "action" part
        # of the models. It's just the window and the number of extra inputs.
        # This will be reshaped when necessary in the creation of each model.
        self.input_shape = (
            (self.window, len(candles), self.num_indicators),
            (self.window, self.num_extra_inputs),
        )
        # This is just for logging (TODO: maybe it can be done differently?)
        self.num_training_episodes = num_episodes

    def step(self, action_id):

        # if an illegal action is taken, the correct it
        action_id = self._correct_action(action_id)
        # update pos according to action
        old_pos = self.pos
        self.pos = self.pos + self.actions[action_id]

        # get current and next indexes
        # TODO: clean this
        self.current_index = self.rand_start_index + self.t
        self.current_time = self.df.index[self.current_index]
        self.next_index = self.current_index + 1
        self.next_time = self.df.index[self.next_index]

        # get current and next prices
        price = self.prices.loc[self.current_time]
        price_next = self.prices.loc[self.next_time]

        # update account and total number of coins according to action
        if self.actions[action_id] == 1:  # if action is buy
            self.total = self.total + self.account / price * (1 - self.fee)
            self.account = 0
        elif self.actions[action_id] == -1:  # if action is sell
            self.account = self.account + price * self.total * (1 - self.fee)
            self.total = 0

        # this variable keeps whether any buy or sell action is taken
        action_taken = np.abs(self.actions[action_id])

        # update action history
        self.df.loc[self.next_time, "action"] = self.actions[action_id]
        self.df.loc[self.next_time, "position"] = old_pos

        # calculate current asset
        asset = self._calculate_asset(price)

        # gain is the profit from the beginning
        self.gain = (asset - self.initial_account) / self.initial_account

        # update profit history
        self.df.loc[self.next_time, "gain"] = self.gain

        # reward computation
        if self.actions[action_id] == 1:
            reward = price_next - price
        elif self.actions[action_id] == -1:
            reward = -1.0 * (price_next - price) ** 2 * np.sign(price_next - price)
        else:
            if self.pos == 0:
                reward = -1.0 * (price_next - price) ** 2 * np.sign(price_next - price)
            else:
                reward = price_next - price
        reward = reward / price

        reward_coeff = 100  # percent

        reward = reward_coeff * reward

        # increment number of trades if any buy or sell action is taken
        self.trades += action_taken

        # discount reward by trade cost id any buy or sell action is taken
        reward = reward - action_taken * self.fee

        # increment time
        self.t += 1  # This one restarts at env reset
        self.total_steps += 1

        # We done?
        done = self.current_index == (self.sim_len - self.window - 2)

        # Recompute trading ratio
        self.trade_ratio = self.trades / self.t

        # retrieve the next (consecutive) state
        next_state = self._get_state(first=False)

        return next_state, reward, done, {}

    def reset(self):
        if self.is_random:
            # episode starts between offset and 100 (upper limit)
            # self.rand_start_index = np.random.randint(self.offset, self.data_len-2000)
            self.rand_start_index = np.random.randint(self.offset, 100)
            print(f"Start index: {self.rand_start_index}")
            print(
                f"We are at about {int(self.total_steps / 1000)}k steps of a total of "
                f"{int(self.spec.max_episode_steps * self.num_training_episodes / 1000)}k."
            )
            print(f"The trading ratio has been {self.trade_ratio:.3f}.")
        else:
            self.rand_start_index = 0

        self.pos = 0
        self.account = self.initial_account
        self.total = 0
        self.sim_len = self.data_len
        self.t = 0
        self.gain = 0
        self.trades = 0
        self.episode = self.episode + 1  # increment episode number
        self.current_index = 0
        self.df["action"] = 0  # reset action history
        self.df["position"] = 0
        self.df["gain"] = 0  # reset profit history
        self.trade_ratio = 0

        return self._get_state(first=True)

    def render(self, mode="human", close=False):
        if self.t % 1000 == 0:
            if self.episode_old != self.episode:
                self.episode_old = self.episode
                # TODO: user proper logger
                print('--------------New episode----------------')
            print(f"episode: {self.episode}, step: {self.t}, gain: {self.gain:.2f}, trades: {self.trades}")

    def _calculate_asset(self, price):
        if self.pos == 0:
            return self.account
        else:
            return self.account + self.total * price

    def _get_state(self, first=False):
        if first:
            state = self.df.iloc[
                self.rand_start_index
                + self.t : (self.rand_start_index + self.t + self.window),
                :,
            ]
        else:
            state = self.df.iloc[self.next_index : (self.next_index + self.window), :]

        # Reshape to 3D
        input1 = state.iloc[:, : -self.num_extra_inputs].values
        input1 = np.reshape(
            input1, newshape=[len(self.candles), self.window, self.num_indicators]
        )
        # Put window (time variable) first
        input1 = np.swapaxes(input1, 0, 1)
        # Put candles variable second
        input1 = np.swapaxes(input1, 1, 2)
        input2 = state.iloc[:, -self.num_extra_inputs:].values

        return {"Input_1": input1, "Input_2": input2}

    def _correct_action(self, action_id):
        # correction
        if self.pos == 0 and (self.actions[action_id] == -1):
            action_id = 1
        elif self.pos == 1 and (self.actions[action_id] == 1):
            action_id = 1
        return action_id
