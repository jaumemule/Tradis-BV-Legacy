# This script creates the RL model

from os import path, mkdir

from rl_fork.agents.dqn import DQNAgent
from rl_fork.agents.sarsa import SARSAAgent
from rl_fork.agents.cem import CEMAgent
from keras.optimizers import Adam
from rl_fork.processors import MultiInputProcessor


class AgentWrapper:
    agent = None

    def __init__(self, env, which):
        self.env = env
        self.which = which

    def create(self, **kwargs):
        model = kwargs['model']
        memory = kwargs['memory']
        warmup_steps = kwargs['warmup_steps']

        if self.which == 'dqn':

            # Deep Q-learning agent
            policy = kwargs['policy']
            processor = MultiInputProcessor(nb_inputs=2)
            self.agent = DQNAgent(model=model, nb_actions=self.env.action_size,
                                  memory=memory, nb_steps_warmup=warmup_steps,
                                  processor=processor,
                                  target_model_update=1e-2, policy=policy)

        elif self.which == 'sarsa':

            # State–action–reward–state–action agent
            policy = kwargs['policy']
            test_policy = kwargs['test_policy']
            processor = MultiInputProcessor(nb_inputs=2)
            self.agent = SARSAAgent(model=model, nb_actions=self.env.action_size,
                                    policy=policy, test_policy=test_policy,
                                    processor=processor,
                                    nb_steps_warmup=warmup_steps)

        elif self.which == 'cem':

            # Cross-entropy method agent
            processor = MultiInputProcessor(nb_inputs=2)
            self.agent = CEMAgent(model=model, nb_actions=self.env.action_size,
                                  processor=processor,
                                  memory=memory, nb_steps_warmup=warmup_steps)

    def compile(self, lr):

        # The Keras-rl library is not very robust and makes us do stupid things like:
        try:
            self.agent.compile(Adam(lr=lr), metrics=['mse'])
        except TypeError:
            # For the cem models
            self.agent.compile()

    def fit(self, steps):
        self.agent.fit(self.env, nb_steps=steps, visualize=True, verbose=0)

    def save(self, file_name):

        if not path.exists("agents"):
            mkdir("agents")

        self.agent.save_weights(file_name,
                                overwrite=True)

    def load_weights(self, w_file_name):
        self.agent.load_weights(w_file_name)

    def test(self, env):
        return self.agent.test(env, nb_episodes=1, action_repetition=1, callbacks=None,
                               visualize=True, nb_max_episode_steps=None,
                               nb_max_start_steps=0, start_step_policy=None, verbose=1)

    def forward(self, observation):
        return self.agent.forward(observation)
