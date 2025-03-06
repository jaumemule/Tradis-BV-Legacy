import pandas as pd
import numpy as np
import gym


class KerasEnvironment(gym.Env):
    metadata = {"render.modes": ["human"]}
    data_len = None

    def __init__(self):
        self.actions = [-1, 0, 1]  # sell, sit, buy
        self.data_features = None  # holds feature names
        self.state_size = None  # input state size
        self.action_size = len(self.actions)  # action size
        self.df = None  # data frame which holds data features and close price
        self.initial_account = 100  # dollars
        self.offset = 20  # any episode does not start before the offset
        self.rand_start_index = 0  # random starting index of the episode
        self.pos = np.array([0])  # position: 1 - traded, 0 - no trade
        self.account = self.initial_account  # running account
        self.total = 0  # total number of coins
        self.done = 0  # flag indicating the end of the simulation
        self.t = 0  # time index
        self.gain = 0  # running profit
        self.episode = 0  # episode number
        self.episode_old = 0  # previous episode number
        self.trades = 0  # number of trades
        self.observation_space = None  # observation space
        self.input_shape = None  # input shape for the deep network
        self.trade_cost = 0  # trading cost
        self.current_index = 0  # current time index
        self.is_random = True  # random start

    def step(self, action_id):

        # if an illegal action is taken, the correct it
        action_id = self.correct_action(action_id)
        # update pos according to action
        self.pos[0] = self.pos[0] + self.actions[action_id]

        # get current and next indexes
        self.current_index = self.rand_start_index + self.t
        next_index = self.current_index + 1

        # retrieve next state line from the data frame
        next_state_line = self.df[self.data_features].iloc[next_index]

        # get current and next prices
        price = self.df.iloc[self.current_index]["close"]
        price_next = self.df.iloc[next_index]["close"]

        # update account and total number of coins according to action
        if self.actions[action_id] == 1:  # if action is buy
            self.total = self.total + self.account / price
            self.account = 0
        elif self.actions[action_id] == -1:  # if action is sell
            self.account = self.account + price * self.total
            self.total = 0

        # this variable keeps whether any buy or sell action is taken
        action_taken = np.abs(self.actions[action_id])

        # update action history
        self.df.at[self.current_index, "action"] = self.actions[action_id]

        # calculate current asset
        asset = self.__calculate_asset(price)

        # gain is the profit from the beginning
        self.gain = (asset - self.initial_account) / self.initial_account * 100

        # update profit history
        self.df.at[self.current_index, "profit"] = self.gain

        # ----- immediate reward calculation algorithm ---------
        if self.actions[action_id] == 1:
            reward = price_next - price
        elif self.actions[action_id] == -1:
            reward = -1.0 * (price_next - price)
        else:
            if self.pos[0] == 0:
                reward = -1.0 * (price_next - price)
            else:
                reward = price_next - price
        reward = reward / price

        reward_coef = 100  # percent

        reward = reward_coef * reward
        # ---------------------------------------------------

        # increment number of trades if any buy or sell action is taken
        self.trades = self.trades + action_taken

        # discount reward by trade cost id any buy or sell action is taken
        reward = reward - action_taken * self.trade_cost

        # increment time
        self.t = self.t + 1

        # construct next state (we also add our position (pos: 0 or 1) to the state)
        next_state = np.append(next_state_line.to_numpy(), self.pos, axis=None).reshape(
            1, self.state_size
        )

        return next_state, reward, True, {}

    def reset(self):

        self.rand_start_index = 0
        self.pos = np.array([0])
        self.account = self.initial_account
        self.total = 0
        self.done = 0
        self.t = 0
        self.gain = 0
        self.trades = 0
        self.episode = 0
        self.current_index = 0

        return True

    def render(self, mode="human", close=False):
        if self.current_index % 100 == 0:
            if self.episode_old != self.episode:
                self.episode_old = self.episode
                print("--------------v0----------------")
            print(
                "episode: {}, time: {}, gain: {:.2f}, trades: {}".format(
                    self.episode, self.current_index, self.gain, self.trades
                )
            )

    def __calculate_asset(self, price):
        if self.pos[0] == 0:
            return self.account
        else:
            return self.account + self.total * price

    def __get_state(self):
        state_line = self.df[self.data_features].iloc[self.rand_start_index + self.t]

        state = np.append(state_line.to_numpy(), self.pos, axis=None).reshape(
            1, self.state_size
        )

        return state

    def correct_action(self, action_id):
        # correction
        if self.pos[0] == 0 and (self.actions[action_id] == -1):
            action_id = 1
        elif self.pos[0] == 1 and (self.actions[action_id] == 1):
            action_id = 1
        return action_id
