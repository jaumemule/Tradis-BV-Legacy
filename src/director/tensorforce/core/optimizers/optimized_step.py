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
from tensorforce.core.optimizers import MetaOptimizer
from tensorforce.core.optimizers.solvers import solver_modules


class OptimizedStep(MetaOptimizer):
    """
    The optimized-step optimizer applies line search to the proposed optimization step of  
    another optimizer to find a more optimal step size.
    """

    def __init__(
        self, name, optimizer, ls_max_iterations=10, ls_accept_ratio=0.9, ls_mode='exponential',
        ls_parameter=0.5, ls_unroll_loop=False, summary_labels=None
    ):
        """
        Optimized-step optimizer constructor.

        Args:
            ls_max_iterations (int > 0): Maximum number of line search iterations.
            ls_accept_ratio: Line search acceptance ratio.
            ls_mode: Line search mode, see LineSearch solver.
            ls_parameter: Line search parameter, see LineSearch solver.
            ls_unroll_loop (bool): Whether to unroll the line search loop (default: false).
        """
        super().__init__(name=name, optimizer=optimizer)

        self.solver = self.add_module(
            name='line-search', module='line_search', modules=solver_modules,
            max_iterations=ls_max_iterations, accept_ratio=ls_accept_ratio, mode=ls_mode,
            parameter=ls_parameter, unroll_loop=ls_unroll_loop
        )

    def tf_step(self, variables, arguments, fn_loss, fn_reference=None, **kwargs):
        augmented_arguments = dict(arguments)

        if fn_reference is not None:
            # Set reference to compare with at each step, in case of a comparative loss.
            reference = fn_reference(**arguments)  # ?????????????????????????????????????????????

            assert 'reference' not in augmented_arguments
            augmented_arguments['reference'] = reference

        # Negative value since line search maximizes.
        loss_before = -fn_loss(**augmented_arguments)

        with tf.control_dependencies(control_inputs=(loss_before,)):
            deltas = self.optimizer.step(
                variables=variables, arguments=arguments, fn_loss=fn_loss,  # no reference here?
                return_estimated_improvement=True, **kwargs
            )

            if isinstance(deltas, tuple):
                # If 'return_estimated_improvement' argument exists.
                if len(deltas) != 2:
                    raise TensorforceError("Unexpected output of internal optimizer.")
                deltas, estimated_improvement = deltas
                # Negative value since line search maximizes.
                estimated_improvement = -estimated_improvement
            else:
                estimated_improvement = None

        with tf.control_dependencies(control_inputs=deltas):
            # Negative value since line search maximizes.
            loss_step = -fn_loss(**augmented_arguments)

        with tf.control_dependencies(control_inputs=(loss_step,)):

            def evaluate_step(deltas):
                with tf.control_dependencies(control_inputs=deltas):
                    applied = self.apply_step(variables=variables, deltas=deltas)
                with tf.control_dependencies(control_inputs=(applied,)):
                    # Negative value since line search maximizes.
                    return -fn_loss(**augmented_arguments)

            return self.solver.solve(
                fn_x=evaluate_step, x_init=deltas, base_value=loss_before, target_value=loss_step,
                estimated_improvement=estimated_improvement
            )
