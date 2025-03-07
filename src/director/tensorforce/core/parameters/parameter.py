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

import tensorflow as tf

from tensorforce import TensorforceError
from tensorforce.core import Module


class Parameter(Module):
    """
    Base class for dynamic hyperparameters.

    Args:
        name (string): Module name
            (<span style="color:#0000C0"><b>internal use</b></span>).
        dtype ("bool" | "int" | "long" | "float"): Tensor type
            (<span style="color:#C00000"><b>required</b></span>).
        shape (iter[int > 0]): Tensor shape
            (<span style="color:#00C000"><b>default</b></span>: scalar).
        summary_labels ('all' | iter[string]): Labels of summaries to record
            (<span style="color:#00C000"><b>default</b></span>: inherit value of parent module).
    """

    def __init__(self, name, dtype, shape=(), summary_labels=None):
        super().__init__(name=name, summary_labels=summary_labels)

        self.dtype = dtype
        self.shape = shape

        Module.register_tensor(
            name=self.name, spec=dict(type=self.dtype, shape=self.shape), batched=False
        )

    def get_parameter_value(self):
        raise NotImplementedError

    def tf_initialize(self):
        super().tf_initialize()

        default = self.get_parameter_value()

        # Temporarily leave module variable scope, otherwise placeholder name is unnecessarily long
        if self.device is not None:
            raise TensorforceError.unexpected()

        self.scope.__exit__(None, None, None)
        self.parameter_input = self.add_placeholder(
            name=self.name, dtype=self.dtype, shape=self.shape, batched=False, default=default
        )
        self.scope.__enter__()

    def tf_value(self):
        parameter = tf.identity(input=self.parameter_input)

        parameter = self.add_summary(label='parameters', name='value', tensor=parameter)

        # Required for TensorFlow optimizers learning_rate
        if Module.global_tensors is not None:
            Module.update_tensor(name=self.name, tensor=parameter)

        return parameter
