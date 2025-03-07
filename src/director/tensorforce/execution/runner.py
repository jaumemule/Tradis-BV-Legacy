# Copyright 2018 Tensorforce Team. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import time
from tqdm import tqdm

import numpy as np

from tensorforce import util
from tensorforce.agents import Agent
from tensorforce.environments import Environment


class Runner(object):

    def __init__(self, agent, environment, evaluation_environment=None):
        self.is_environment_external = isinstance(environment, Environment)
        self.environment = Environment.create(environment=environment)
        self.is_agent_external = isinstance(agent, Agent)
        self.agent = Agent.create(agent=agent, environment=self.environment)
        self.is_eval_environment_external = isinstance(evaluation_environment, Environment)
        if evaluation_environment is None:
            self.evaluation_environment = None
        else:
            self.evaluation_environment = Environment.create(environment=evaluation_environment)

        self.agent.initialize()
        self.global_episode = self.agent.episode
        self.global_timestep = self.agent.timestep
        self.episode_rewards = list()
        self.episode_timesteps = list()
        self.episode_seconds = list()

    def close(self):
        if hasattr(self, 'tqdm'):
            self.tqdm.close()
        if not self.is_agent_external:
            self.agent.close()
        if not self.is_environment_external:
            self.environment.close()
        if self.evaluation_environment is not None and not self.is_eval_environment_external:
            self.evaluation_environment.close()

    # TODO: make average reward another possible criteria for runner-termination
    def run(
        self,
        # General
        num_episodes=None, num_timesteps=None, max_episode_timesteps=None, num_repeat_actions=1,
        # Callback
        callback=None, callback_episode_frequency=None, callback_timestep_frequency=None,
        # Tqdm
        use_tqdm=True, mean_horizon=10,
        # Evaluation
        evaluation=False, evaluation_callback=None, evaluation_frequency=None,
        update_as_evaluation_frequency=False, max_evaluation_timesteps=None,
        num_evaluation_iterations=1, save_best_agent=False
    ):
        # General
        if num_episodes is None:
            self.num_episodes = float('inf')
        else:
            self.num_episodes = num_episodes
        if num_timesteps is None:
            self.num_timesteps = float('inf')
        else:
            self.num_timesteps = num_timesteps
        if max_episode_timesteps is None:
            self.max_episode_timesteps = float('inf')
        else:
            self.max_episode_timesteps = max_episode_timesteps
        self.num_repeat_actions = num_repeat_actions

        # Callback
        assert callback_episode_frequency is None or callback_timestep_frequency is None
        if callback_episode_frequency is None and callback_timestep_frequency is None:
            callback_episode_frequency = 1
        if callback_episode_frequency is None:
            self.callback_episode_frequency = float('inf')
        else:
            self.callback_episode_frequency = callback_episode_frequency
        if callback_timestep_frequency is None:
            self.callback_timestep_frequency = float('inf')
        else:
            self.callback_timestep_frequency = callback_timestep_frequency
        if callback is None:
            self.callback = (lambda r: True)
        elif util.is_iterable(x=callback):
            def sequential_callback(runner):
                result = True
                for fn in callback:
                    x = fn(runner)
                    if isinstance(result, bool):
                        result = result and x
                return result
            self.callback = sequential_callback
        else:
            def boolean_callback(runner):
                result = callback(runner)
                if isinstance(result, bool):
                    return result
                else:
                    return True
            self.callback = boolean_callback

        # Tqdm
        if use_tqdm:
            if hasattr(self, 'tqdm'):
                self.tqdm.close()

            assert self.num_episodes != float('inf') or self.num_timesteps != float('inf')
            inner_callback = self.callback

            if self.num_episodes != float('inf'):
                # Episode-based tqdm (default option if both num_episodes and num_timesteps set)
                assert self.num_episodes != float('inf')
                self.tqdm = tqdm(
                    desc='Episodes', total=self.num_episodes, initial=self.global_episode,
                    postfix={
                        'reward': '{:.2f}'.format(0.0), 'ts/ep': str(0),
                        'sec/ep': '{:.2f}'.format(0.0), 'ms/ts': '{:.1f}'.format(0.0)
                    }
                )
                self.tqdm_last_update = self.global_episode

                def tqdm_callback(runner):
                    mean_reward = float(np.mean(runner.episode_rewards[-mean_horizon:]))
                    mean_ts_per_ep = int(np.mean(runner.episode_timesteps[-mean_horizon:]))
                    mean_sec_per_ep = float(np.mean(runner.episode_seconds[-mean_horizon:]))
                    mean_ms_per_ts = mean_sec_per_ep * 1000.0 / mean_ts_per_ep
                    runner.tqdm.set_postfix({
                        'reward': '{:.2f}'.format(mean_reward), 'ts/ep': str(mean_ts_per_ep),
                        'sec/ep': '{:.2f}'.format(mean_sec_per_ep),
                        'ms/ts': '{:.1f}'.format(mean_ms_per_ts)
                    })
                    runner.tqdm.update(n=(runner.global_episode - runner.tqdm_last_update))
                    runner.tqdm_last_update = runner.global_episode
                    return inner_callback(runner)

            else:
                # Timestep-based tqdm
                assert self.num_timesteps != float('inf')
                self.tqdm = tqdm(
                    desc='Timesteps', total=self.num_timesteps, initial=self.global_timestep,
                    postfix=dict(mean_reward='n/a')
                )
                self.tqdm_last_update = self.global_timestep

                def tqdm_callback(runner):
                    # sum_timesteps_reward = sum(runner.timestep_rewards[num_mean_reward:])
                    # num_timesteps = min(num_mean_reward, runner.episode_timestep)
                    # mean_reward = sum_timesteps_reward / num_episodes
                    runner.tqdm.set_postfix(mean_reward='n/a')
                    runner.tqdm.update(n=(runner.global_timestep - runner.tqdm_last_update))
                    runner.tqdm_last_update = runner.global_timestep
                    return inner_callback(runner)

            self.callback = tqdm_callback

        # Evaluation
        self.evaluation = evaluation
        if evaluation_callback is None:
            self.evaluation_callback = (lambda r: None)
        else:
            assert not self.evaluation
            self.evaluation_callback = evaluation_callback
        if evaluation_frequency is None:
            if update_as_evaluation_frequency:
                assert evaluation_frequency is None
                batch_size = self.agent.model.update_mode['batch_size']
                frequency = self.agent.model.update_mode.get('frequency', batch_size)
                if self.agent.model.update_unit == 'episodes':
                    self.evaluation_frequency = frequency
                else:
                    # Approximates maximum number of episodes for an update to happen
                    self.evaluation_frequency = frequency // self.max_episode_timesteps
            else:
                self.evaluation_frequency = float('inf')
        else:
            assert not self.evaluation and not update_as_evaluation_frequency
            self.evaluation_frequency = evaluation_frequency
        if max_evaluation_timesteps is None:
            self.max_evaluation_timesteps = float('inf')
        else:
            assert not self.evaluation
            self.max_evaluation_timesteps = max_evaluation_timesteps
        self.num_evaluation_iterations = num_evaluation_iterations
        self.save_best_agent = save_best_agent
        if self.save_best_agent:
            assert not self.evaluation
            inner_evaluation_callback = self.evaluation_callback

            def mean_reward_callback(runner):
                result = inner_evaluation_callback(runner)
                if result is None:
                    return float(np.mean(runner.evaluation_rewards))
                else:
                    return result

            self.evaluation_callback = mean_reward_callback
            self.best_evaluation_score = None

        # Reset agent
        self.agent.reset()

        # Episode counter
        self.episode = 1

        # Episode loop
        while True:
            # Run episode
            if not self.run_episode(
                environment=self.environment, max_timesteps=self.max_episode_timesteps,
                evaluation=self.evaluation
            ):
                return

            # Update experiment statistics
            self.episode_rewards.append(self.episode_reward)
            self.episode_timesteps.append(self.episode_timestep)
            self.episode_seconds.append(self.episode_second)

            # Run evaluation
            if self.episode % self.evaluation_frequency == 0:
                if self.evaluation_environment is None:
                    environment = self.environment
                else:
                    environment = self.evaluation_environment

                self.evaluation_rewards = list()
                self.evaluation_timesteps = list()
                self.evaluation_seconds = list()

                # Evaluation loop
                for _ in range(self.num_evaluation_iterations):
                    self.run_episode(
                        environment=environment, max_timesteps=self.max_evaluation_timesteps,
                        evaluation=True
                    )

                    self.evaluation_rewards.append(self.episode_reward)
                    self.evaluation_timesteps.append(self.episode_timestep)
                    self.evaluation_seconds.append(self.episode_second)

                # Evaluation callback
                if self.save_best_agent:
                    evaluation_score = self.evaluation_callback(self)
                    assert isinstance(evaluation_score, float)
                    if self.best_evaluation_score is None:
                        self.best_evaluation_score = evaluation_score
                    elif evaluation_score > self.best_evaluation_score:
                        self.best_evaluation_score = evaluation_score
                        self.agent.save(filename='best-model', append_timestep=False)
                else:
                    self.evaluation_callback(self)

            # Update global timestep/episode
            self.global_timestep = self.agent.timestep
            self.global_episode = self.agent.episode

            # Callback
            if self.episode % self.callback_episode_frequency == 0 and not self.callback(self):
                return

            # Terminate experiment if too long
            if self.global_timestep >= self.num_timesteps:
                return
            elif self.global_episode >= self.num_episodes:
                return
            elif self.agent.should_stop():
                return

            # Increment episode counter (after calling callback)
            self.episode += 1

    def run_episode(self, environment, max_timesteps, evaluation):
        # Episode statistics
        self.episode_reward = 0
        self.episode_timestep = 0
        episode_start = time.time()

        # Start environment episode
        states = environment.reset()

        # Timestep loop
        while True:
            # Retrieve actions from agent
            actions = self.agent.act(states=states, evaluation=evaluation)
            self.episode_timestep += 1
            # Execute actions in environment (optional repeated execution)
            reward = 0.0
            for _ in range(self.num_repeat_actions):
                states, terminal, step_reward = environment.execute(actions=actions)
                reward += step_reward
                if terminal:
                    break
            self.episode_reward += reward

            # Terminate episode if too long
            if self.episode_timestep >= max_timesteps:
                terminal = True

            # Observe unless evaluation
            if not evaluation:
                self.agent.observe(terminal=terminal, reward=reward)

            # Callback
            if self.episode_timestep % self.callback_timestep_frequency == 0 and \
                    not self.callback(self):
                return False

            # Episode termination check
            if terminal:
                break

            # No callbacks for evaluation
            if evaluation:
                continue

            # Update global timestep/episode
            self.global_timestep = self.agent.timestep
            self.global_episode = self.agent.episode

            # Terminate experiment if too long
            if self.global_timestep >= self.num_timesteps:
                return
            elif self.global_episode >= self.num_episodes:
                return
            elif self.agent.should_stop():
                return False

        # Update episode statistics
        self.episode_second = time.time() - episode_start

        return True
