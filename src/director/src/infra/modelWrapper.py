# This script creates the architecture for the neural nets that the RL is going to use

import os

from keras.models import Sequential
from keras.layers import (
    Dense,
    Activation,
    Flatten,
    Dropout,
    LSTM,
    Concatenate,
)
from keras.layers import Conv2D, MaxPooling2D, Reshape
from keras.constraints import max_norm
from keras import regularizers, Input, Model
from keras.utils import plot_model

def create_model(env):
    # In principle this is deprecated in favour of the model_build_original

    dropout_prob = 0.3  # aggressive dropout regularization
    num_units = 1024  # number of neurons in the hidden units

    model = Sequential()
    model.add(Flatten(input_shape=(1,) + env.state_shape))
    model.add(Dense(num_units))
    model.add(Activation("relu"))

    model.add(Dense(num_units))
    model.add(Dropout(dropout_prob))
    model.add(Activation("relu"))

    model.add(Dense(env.action_size))
    model.add(Activation("softmax"))
    print(model.summary())
    return model


class ModelWrapper:
    MODEL_DETAILS = False
    # Basically for debugging - careful with the pydot installation
    PLOT_MODEL = False # Not working in the google machines because of stupid pydot (FIXME)

    def __init__(self, env, cfg):

        # network constants
        self.max_bias = cfg["network"]["max_bias"]
        self.maxi_norm = cfg["network"]["maxi_norm"]

        # env parameters
        self.state_shape = tuple(cfg['about_data']['state_shape'])
        self.history_shape = tuple(cfg['about_data']['history_shape'])
        self.action_size = env.action_size

        # network fixmes
        self.name = ""
        self.kernel_size = cfg["network"]["kernel_size"]
        self.pooling_size = cfg["network"]["pooling_size"]

        # Activations
        self.inner_act = cfg["network"]["inner_activation"]
        self.final_act = cfg["network"]["final_activation"]

        # Others
        self.history_units = cfg["network"]["history_units"]
        self.batch_normalization = cfg["network"]["batch_normalization"]

    @staticmethod
    def _plot_models(model):
        _name = "model_architectures"
        if not os.path.exists(_name):
            os.mkdir(_name)
        _path = os.path.join(_name, f"{model.name}.png")
        plot_model(model, _path, show_shapes=True)

    def _build_main_nn(self, which, parameters):

        print("Building model " + str(which))

        if which == "lstm":
            return self.build_model_lstm(parameters)

        elif which == "reg_lstm":
            return self.build_model_reg_lstm(parameters)

        elif which == "cnn":
            return self.build_model_cnn(parameters)

        elif which == "yang":
            return self.build_model_yang(parameters)

        elif which == "baseline":
            return self.build_model_baseline(parameters)

        elif which == "abe":
            return self.build_model_abe(parameters)

        elif which == "original":
            return self.build_model_original(parameters)

        else:
            raise ModuleNotFoundError("Model doesn't exist. Exiting.")

    def _build_secondary_nn(self):
        inputs2 = Input((1,) + self.history_shape, name="Input_2")
        x2 = Flatten()(inputs2)
        x2 = Dense(self.history_units, activation=self.inner_act)(x2)

        return inputs2, x2

    def build_model(self, which, parameters):

        # main model
        inputs1, outputs1 = self._build_main_nn(which, parameters)
        # history-action model
        inputs2, outputs2 = self._build_secondary_nn()

        x = Concatenate(axis=-1)([outputs1, outputs2])
        outputs = Dense(self.action_size, activation=self.final_act)(x)

        model = Model(inputs=[inputs1, inputs2], outputs=outputs, name=which)

        if self.MODEL_DETAILS:
            print(model.summary())
            if self.PLOT_MODEL:
                self._plot_models(model)

        return model

    def build_model_original(self, parameters):

        # This is the original from the posts
        # Original dropout is 0.8 and inner_units is 256

        inner_units = parameters["inner_units"]
        dense_units = parameters["dense_units"]
        dropout = parameters["dropout"]

        inputs = Input((1,) + self.state_shape, name="Input_1")
        x = Flatten()(inputs)
        x = Dense(dense_units, activation=self.inner_act)(x)
        x = Dropout(dropout)(x)
        x = Dense(inner_units, activation=self.inner_act)(x)
        x = Dropout(dropout)(x)

        return inputs, x

    def build_model_lstm(self, parameters):

        inner_units = parameters["inner_units"]
        dense_units = parameters["dense_units"]
        dropout = parameters["dropout"]

        inputs = Input((1,) + self.state_shape, name="Input_1")
        x = Reshape((self.state_shape[0], self.state_shape[1] * self.state_shape[2]))(
            inputs
        )
        x = LSTM(units=inner_units, return_sequences=True)(x)
        x = Dropout(dropout)(x)
        x = LSTM(units=inner_units, return_sequences=False)(x)
        x = Dropout(dropout)(x)
        x = Dense(dense_units, activation=self.inner_act)(x)

        return inputs, x

    def build_model_reg_lstm(self, parameters):

        inner_units = parameters["inner_units"]
        dense_units = parameters["dense_units"]
        dropout_1 = parameters["dropout_1"]
        dropout_2 = parameters["dropout_2"]
        l1 = parameters["l1"]
        l2 = parameters["l2"]

        maxi_norm = self.maxi_norm

        inputs = Input((1,) + self.state_shape, name="Input_1")

        x = Reshape((self.state_shape[0], self.state_shape[1] * self.state_shape[2]))(
            inputs
        )
        x = LSTM(
            units=inner_units,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1(l1),
            kernel_regularizer=regularizers.l2(l2),
            kernel_constraint=max_norm(maxi_norm),
            return_sequences=True,
        )(x)
        x = Dropout(dropout_1)(x)
        x = LSTM(
            units=inner_units,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1(l1),
            kernel_regularizer=regularizers.l2(l2),
            kernel_constraint=max_norm(maxi_norm),
            return_sequences=False,
        )(x)
        x = Dropout(dropout_1)(x)
        x = Dense(
            dense_units,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(maxi_norm),
            activation=self.inner_act,
        )(x)
        x = Dropout(dropout_2)(x)

        return inputs, x

    def build_model_cnn(self, parameters):

        inner_units = parameters["inner_units"]
        dense_units = parameters["dense_units"]
        dropout_1 = parameters["dropout_1"]
        dropout_2 = parameters["dropout_2"]
        l1 = parameters["l1"]
        l2 = parameters["l2"]

        inputs = Input((1,) + self.state_shape, name="Input_1")
        x = Reshape((self.state_shape[0], self.state_shape[1], self.state_shape[2]))(
            inputs
        )
        x = Conv2D(
            inner_units,
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_1)(x)
        x = Conv2D(
            inner_units,
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_1)(x)
        x = Flatten()(x)
        x = Dense(
            dense_units,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            activation=self.inner_act,
        )(x)
        x = Dropout(dropout_2)(x)

        return inputs, x

    def build_model_yang(self, parameters):

        dropout_1 = parameters["dropout_1"]
        dropout_2 = parameters["dropout_2"]
        l1 = parameters["l1"]
        l2 = parameters["l2"]
        # The inner unit count of layers is different here to mimic the paper, which
        # works with size = 1
        size = parameters["size"]

        inputs = Input((1,) + self.state_shape, name="Input_1")

        x = Reshape((self.state_shape[0], self.state_shape[1], self.state_shape[2]))(
            inputs
        )
        x = Conv2D(
            int(50 * size),
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_1)(x)
        x = Conv2D(
            int(40 * size),
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_1)(x)
        x = Conv2D(
            int(20 * size),
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_2)(x)
        x = Flatten()(x)

        return inputs, x

    def build_model_abe(self, parameters):
        # https://arxiv.org/ftp/arxiv/papers/1801/1801.01777.pdf

        dropout_1 = parameters["dropout_1"]
        dropout_2 = parameters["dropout_2"]
        l1 = parameters["l1"]
        l2 = parameters["l2"]
        # The inner unit count of layers is different here to mimic the paper, which
        # works with size = 1
        size = parameters["size"]

        inputs = Input((1,) + self.state_shape, name="Input_1")

        x = Reshape((self.state_shape[0], self.state_shape[1], self.state_shape[2]))(
            inputs
        )
        x = Conv2D(
            int(100 * size),
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_1)(x)
        x = Conv2D(
            int(50 * size),
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_1)(x)
        x = Conv2D(
            int(10 * size),
            input_shape=self.state_shape,
            kernel_size=self.kernel_size,
            activation=self.inner_act,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            bias_constraint=max_norm(self.max_bias),
        )(x)
        x = MaxPooling2D(pool_size=self.pooling_size)(x)
        x = Dropout(dropout_2)(x)
        x = Flatten()(x)

        return inputs, x

    def build_model_baseline(self, parameters):

        dense_units = parameters["dense_units"]
        dropout = parameters["dropout"]
        l1 = parameters["l1"]
        l2 = parameters["l2"]

        inputs = Input((1,) + self.state_shape, name="Input_1")
        x = Flatten()(inputs)
        x = Dense(
            dense_units,
            activity_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
            kernel_constraint=max_norm(self.maxi_norm),
            activation=self.inner_act,
        )(x)
        x = Dropout(dropout)(x)

        return inputs, x
