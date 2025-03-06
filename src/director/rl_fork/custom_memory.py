from __future__ import absolute_import
from collections import deque, namedtuple
import warnings
import random
import numpy as np
from math import ceil, floor
from rl_fork.memory import RingBuffer, Memory, zeroed_observation, sample_batch_indexes

# This is to be understood as a transition: Given `state0`, performing `action`
# yields `reward` and results in `state1`, which might be `terminal`.
Experience = namedtuple('Experience', 'state0, action, reward, state1, terminal1')

def sample_batch_indexes_from_weigted_lists(low, high, size, list_more, list_less, proba):
    if high - low >= size:
        try:
            r = xrange(low, high)
        except NameError:
            r = range(low, high)
        positive_n = ceil(proba*size)
        negative_n = floor((1-proba)*size)
        list_more = list(filter(lambda x: x > low and x < high, list_more))
        list_less = list(filter(lambda x: x > low and x < high, list_less))
        if positive_n < len(list_more):
            pos_idxs = random.sample(list_more, positive_n)
        else:
            pos_idxs = list_more
        if negative_n < len(list_less):
            neg_idxs = random.sample(list_less, negative_n)
        else:
            neg_idxs = list_less
        batch_idxs = pos_idxs + neg_idxs
    while len(batch_idxs) < size:
        batch_idxs += random.sample(r, 1)
    assert len(batch_idxs) == size
    return batch_idxs

class PosNegSequentialMemory(Memory):
    def __init__(self, limit, pos_proba=0.7, threshold=0, **kwargs):
        super(PosNegSequentialMemory, self).__init__(**kwargs)

        self.limit = limit

        # Do not use deque to implement the memory. This data structure may seem convenient but
        # it is way too slow on random access. Instead, we use our own ring buffer implementation.
        self.actions = RingBuffer(limit)
        self.rewards = RingBuffer(limit)
        self.terminals = RingBuffer(limit)
        self.observations = RingBuffer(limit)
        self.idx_pos = []
        self.idx_neg = []
        self.pos_proba = pos_proba
        self.threshold = threshold

    def sample(self, batch_size, batch_idxs=None):
        """Return a randomized batch of experiences
        # Argument
            batch_size (int): Size of the all batch
            batch_idxs (int): Indexes to extract
        # Returns
            A list of experiences randomly selected
        """
        # It is not possible to tell whether the first state in the memory is terminal, because it
        # would require access to the "terminal" flag associated to the previous state. As a result
        # we will never return this first state (only using `self.terminals[0]` to know whether the
        # second state is terminal).
        # In addition we need enough entries to fill the desired window length.
        assert self.nb_entries >= self.window_length + 2, 'not enough entries in the memory'

        if batch_idxs is None:
            # Draw random indexes such that we have enough entries before each index to fill the
            # desired window length.
            batch_idxs = sample_batch_indexes_from_weigted_lists(
                self.window_length, self.nb_entries - 1, batch_size,
            self.idx_pos, self.idx_neg, self.pos_proba)
        batch_idxs = np.array(batch_idxs) + 1
        assert np.min(batch_idxs) >= self.window_length + 1
        assert np.max(batch_idxs) <= self.nb_entries
        assert len(batch_idxs) == batch_size

        # Create experiences
        experiences = []
        for idx in batch_idxs:
            terminal0 = self.terminals[idx - 2]
            while terminal0:
                # Skip this transition because the environment was reset here. Select a new, random
                # transition and use this instead. This may cause the batch to contain the same
                # transition twice.
                idx = sample_batch_indexes(self.window_length + 1, self.nb_entries, size=1)[0]
                terminal0 = self.terminals[idx - 2]
            # assert self.window_length + 1 <= idx < self.nb_entries

            # This code is slightly complicated by the fact that subsequent observations might be
            # from different episodes. We ensure that an experience never spans multiple episodes.
            # This is probably not that important in practice but it seems cleaner.
            state0 = [self.observations[idx - 1]]
            for offset in range(0, self.window_length - 1):
                current_idx = idx - 2 - offset
                assert current_idx >= 1
                current_terminal = self.terminals[current_idx - 1]
                if current_terminal and not self.ignore_episode_boundaries:
                    # The previously handled observation was terminal, don't add the current one.
                    # Otherwise we would leak into a different episode.
                    break
                state0.insert(0, self.observations[current_idx])
            while len(state0) < self.window_length:
                state0.insert(0, zeroed_observation(state0[0]))
            action = self.actions[idx - 1]
            reward = self.rewards[idx - 1]
            terminal1 = self.terminals[idx - 1]

            # Okay, now we need to create the follow-up state. This is state0 shifted on timestep
            # to the right. Again, we need to be careful to not include an observation from the next
            # episode if the last state is terminal.
            state1 = [np.copy(x) for x in state0[1:]]
            state1.append(self.observations[idx])

            assert len(state0) == self.window_length
            assert len(state1) == len(state0)
            experiences.append(Experience(state0=state0, action=action, reward=reward,
                                          state1=state1, terminal1=terminal1))
        assert len(experiences) == batch_size
        return experiences

    def append(self, observation, action, reward, terminal, training=True):
        """Append an observation to the memory
        # Argument
            observation (dict): Observation returned by environment
            action (int): Action taken to obtain this observation
            reward (float): Reward obtained by taking this action
            terminal (boolean): Is the state terminal
        """
        super(PosNegSequentialMemory, self).append(observation, action, reward, terminal, training=training)

        # This needs to be understood as follows: in `observation`, take `action`, obtain `reward`
        # and weather the next state is `terminal` or not.
        if training:
            self.observations.append(observation)
            self.actions.append(action)
            self.rewards.append(reward)
            self.terminals.append(terminal)
            if reward > self.threshold:
                self.idx_pos.append(self.nb_entries - 1)
                assert self.rewards[self.nb_entries - 1] > self.threshold
            else:
                self.idx_neg.append(self.nb_entries -1)
                assert self.rewards[self.nb_entries - 1] <= self.threshold


    @property
    def nb_entries(self):
        """Return number of observations
        # Returns
            Number of observations
        """
        return len(self.observations)

    def get_config(self):
        """Return configurations of SequentialMemory
        # Returns
            Dict of config
        """
        config = super(PosNegSequentialMemory, self).get_config()
        config['limit'] = self.limit
        return config



class EpisodeParameterMemory(Memory):
    def __init__(self, limit, **kwargs):
        super(EpisodeParameterMemory, self).__init__(**kwargs)
        self.limit = limit

        self.params = RingBuffer(limit)
        self.intermediate_rewards = []
        self.total_rewards = RingBuffer(limit)

    def sample(self, batch_size, batch_idxs=None):
        """Return a randomized batch of params and rewards
        # Argument
            batch_size (int): Size of the all batch
            batch_idxs (int): Indexes to extract
        # Returns
            A list of params randomly selected and a list of associated rewards
        """
        if batch_idxs is None:
            batch_idxs = sample_batch_indexes(0, self.nb_entries, size=batch_size)
        assert len(batch_idxs) == batch_size

        batch_params = []
        batch_total_rewards = []
        for idx in batch_idxs:
            batch_params.append(self.params[idx])
            batch_total_rewards.append(self.total_rewards[idx])
        return batch_params, batch_total_rewards

    def append(self, observation, action, reward, terminal, training=True):
        """Append a reward to the memory
        # Argument
            observation (dict): Observation returned by environment
            action (int): Action taken to obtain this observation
            reward (float): Reward obtained by taking this action
            terminal (boolean): Is the state terminal
        """
        super(EpisodeParameterMemory, self).append(observation, action, reward, terminal, training=training)
        if training:
            self.intermediate_rewards.append(reward)

    def finalize_episode(self, params):
        """Append an observation to the memory
        # Argument
            observation (dict): Observation returned by environment
            action (int): Action taken to obtain this observation
            reward (float): Reward obtained by taking this action
            terminal (boolean): Is the state terminal
        """
        total_reward = sum(self.intermediate_rewards)
        self.total_rewards.append(total_reward)
        self.params.append(params)
        self.intermediate_rewards = []

    @property
    def nb_entries(self):
        """Return number of episode rewards
        # Returns
            Number of episode rewards
        """
        return len(self.total_rewards)

    def get_config(self):
        """Return configurations of SequentialMemory
        # Returns
            Dict of config
        """
        config = super(PosNegSequentialMemory, self).get_config()
        config['limit'] = self.limit
        return config


class PrioritizedMemory(Memory):
    def __init__(self, limit, alpha=.4, start_beta=1., end_beta=1., steps_annealed=1, **kwargs):
        super(PrioritizedMemory, self).__init__(**kwargs)

        #The capacity of the replay buffer
        self.limit = limit

        #Transitions are stored in individual RingBuffers, similar to the SequentialMemory.
        #This does complicate things a bit relative to the OpenAI baseline implementation.
        self.actions = RingBuffer(limit)
        self.rewards = RingBuffer(limit)
        self.terminals = RingBuffer(limit)
        self.observations = RingBuffer(limit)

        assert alpha >= 0
        #how aggressively to sample based on TD error
        self.alpha = alpha
        #how aggressively to compensate for that sampling. This value is typically annealed
        #to stabilize training as the model converges (beta of 1.0 fully compensates for TD-prioritized sampling).
        self.start_beta = start_beta
        self.end_beta = end_beta
        self.steps_annealed = steps_annealed

        #SegmentTrees need a leaf count that is a power of 2
        tree_capacity = 1
        while tree_capacity < self.limit:
            tree_capacity *= 2

        #Create SegmentTrees with this capacity
        self.sum_tree = SumSegmentTree(tree_capacity)
        self.min_tree = MinSegmentTree(tree_capacity)
        self.max_priority = 1.

        #wrapping index for interacting with the trees
        self.next_index = 0

    def append(self, observation, action, reward, terminal, training=True):\
        #super() call adds to the deques that hold the most recent info, which is fed to the agent
        #on agent.forward()
        super(PrioritizedMemory, self).append(observation, action, reward, terminal, training=training)
        if training:
            self.observations.append(observation)
            self.actions.append(action)
            self.rewards.append(reward)
            self.terminals.append(terminal)
            #The priority of each new transition is set to the maximum
            self.sum_tree[self.next_index] = self.max_priority ** self.alpha
            self.min_tree[self.next_index] = self.max_priority ** self.alpha

            #shift tree pointer index to keep it in sync with RingBuffers
            self.next_index = (self.next_index + 1) % self.limit

    def _sample_proportional(self, batch_size):
        #outputs a list of idxs to sample, based on their priorities.
        idxs = list()

        for _ in range(batch_size):
            mass = random.random() * self.sum_tree.sum(0, self.limit - 1)
            idx = self.sum_tree.find_prefixsum_idx(mass)
            idxs.append(idx)

        return idxs

    def sample(self, batch_size, beta=1.):
        idxs = self._sample_proportional(batch_size)

        #importance sampling weights are a stability measure
        importance_weights = list()

        #The lowest-priority experience defines the maximum importance sampling weight
        prob_min = self.min_tree.min() / self.sum_tree.sum()
        max_importance_weight = (prob_min * self.nb_entries)  ** (-beta)
        obs_t, act_t, rews, obs_t1, dones = [], [], [], [], []

        experiences = list()
        for idx in idxs:
            while idx < self.window_length + 1:
                idx += 1

            terminal0 = self.terminals[idx - 2]
            while terminal0:
                # Skip this transition because the environment was reset here. Select a new, random
                # transition and use this instead. This may cause the batch to contain the same
                # transition twice.
                idx = sample_batch_indexes(self.window_length + 1, self.nb_entries, size=1)[0]
                terminal0 = self.terminals[idx - 2]

            assert self.window_length + 1 <= idx < self.nb_entries

            #probability of sampling transition is the priority of the transition over the sum of all priorities
            prob_sample = self.sum_tree[idx] / self.sum_tree.sum()
            importance_weight = (prob_sample * self.nb_entries) ** (-beta)
            #normalize weights according to the maximum value
            importance_weights.append(importance_weight/max_importance_weight)

            # Code for assembling stacks of observations and dealing with episode boundaries is borrowed from
            # SequentialMemory
            state0 = [self.observations[idx - 1]]
            for offset in range(0, self.window_length - 1):
                current_idx = idx - 2 - offset
                assert current_idx >= 1
                current_terminal = self.terminals[current_idx - 1]
                if current_terminal and not self.ignore_episode_boundaries:
                    # The previously handled observation was terminal, don't add the current one.
                    # Otherwise we would leak into a different episode.
                    break
                state0.insert(0, self.observations[current_idx])
            while len(state0) < self.window_length:
                state0.insert(0, zeroed_observation(state0[0]))
            action = self.actions[idx - 1]
            reward = self.rewards[idx - 1]
            terminal1 = self.terminals[idx - 1]
            state1 = [np.copy(x) for x in state0[1:]]
            state1.append(self.observations[idx])

            assert len(state0) == self.window_length
            assert len(state1) == len(state0)
            experiences.append(Experience(state0=state0, action=action, reward=reward,
                                          state1=state1, terminal1=terminal1))
        assert len(experiences) == batch_size

        # Return a tuple whre the first batch_size items are the transititions
        # while -2 is the importance weights of those transitions and -1 is
        # the idxs of the buffer (so that we can update priorities later)
        return tuple(list(experiences)+ [importance_weights, idxs])

    def update_priorities(self, idxs, priorities):
        #adjust priorities based on new TD error
        for i, idx in enumerate(idxs):
            assert 0 <= idx < self.limit
            priority = priorities[i] ** self.alpha
            self.sum_tree[idx] = priority
            self.min_tree[idx] = priority
            self.max_priority = max(self.max_priority, priority)

    def calculate_beta(self, current_step):
        a = float(self.end_beta - self.start_beta) / float(self.steps_annealed)
        b = float(self.start_beta)
        current_beta = min(self.end_beta, a * float(current_step) + b)
        return current_beta

    def get_config(self):
        config = super(PrioritizedMemory, self).get_config()
        config['alpha'] = self.alpha
        config['start_beta'] = self.start_beta
        config['end_beta'] = self.end_beta
        config['beta_steps_annealed'] = self.steps_annealed

    @property
    def nb_entries(self):
        """Return number of observations
        # Returns
            Number of observations
        """
        return len(self.observations)