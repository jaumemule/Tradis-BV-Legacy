from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, Dropout, LSTM, BatchNormalization
from keras.layers import Conv1D, Conv2D, MaxPooling1D, MaxPooling2D, Reshape
from keras.constraints import max_norm
from keras import regularizers


def create_model(env):

    # In principle this is deprecated in favour of the model_build_original

    dropout_prob = 0.5  # aggressive dropout regularization
    num_units = 512  # number of neurons in the hidden units

    model = Sequential()
    model.add(Flatten(input_shape=(1,) + env.input_shape))
    model.add(Dense(num_units))
    model.add(Activation('relu'))

    model.add(Dense(num_units))
    model.add(Dropout(dropout_prob))
    model.add(Activation('relu'))

    model.add(Dense(env.action_size))
    model.add(Activation('softmax'))
    print(model.summary())
    return model


class ModelWrapper(object):

    def __init__(self, env):

        self.input_shape = env.input_shape
        self.seq_len = 1
        self.inner_units = 256
        self.dense_units = 256
        self.size = 1
        self.acion_size = env.action_size
        self.dropout_1 = 0.5
        self.dropout_2 = 0.0
        self.name = ""
        self.kernel_size = 1
        self.pooling_size = 1
        self.l1 = 0
        self.l2 = 0
        self.maxi_norm = 10

    def build_model_(self, which='cnn'):

        print("Building model " + str(which))

        if which == 1:
            return self.build_model_1()

        elif which == 2:
            return self.build_model_2()

        elif which == "lstm":
            return self.build_model_2reg()

        elif which == "cnn":
            return self.build_model_cnn()

        elif which == "yang":
            return self.build_model_yang()

        elif which == "baseline":
            return self.build_model_baseline()

        elif which == "abe":
            return self.build_model_abe()

        elif which == "original":
            return self.build_model_original()

        else:
            # FIXME: I'm reusing the closest error I could find, this needs to be changed
            raise ModuleNotFoundError("Model doesn't exist. Exiting.")

    def build_model_original(self):

        # This is the original from the posts
        # Original dropout is 0.8 and inner_units is 256

        model = Sequential()
        model.add(Flatten(input_shape=(1,) + self.input_shape))
        model.add(Dense(self.inner_units))
        model.add(Activation('relu'))

        model.add(Dense(self.inner_units))
        model.add(Dropout(self.dropout_1))
        model.add(Activation('relu'))

        model.add(Dense(self.acion_size))
        model.add(Activation('softmax'))
        print(model.summary())
        return model

    def build_model_1(self):

        dropout = self.dropout_1
        model = Sequential()
        model.add(Dense(
            units=self.dense_units,
            input_shape=(1, ) + self.input_shape))

        model.add(Activation("softmax"))

        model.add(Reshape(target_shape=(1, self.dense_units,)))

        model.add(LSTM(
            units=self.inner_units,
            return_sequences=True))
        model.add(Dropout(dropout))

        model.add(LSTM(
            self.inner_units,
            return_sequences=False))
        model.add(Dropout(dropout))

        model.add(Dense(
            units=self.acion_size))
        model.add(Activation("softmax"))

        print(model.summary())
        return model

    def build_model_2(self):

        dropout = self.dropout_1
        maxi_norm = self.maxi_norm

        model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

        model.add(Dense(units=self.dense_units,  # dense units (changeable)
                        input_shape=(1,) + self.input_shape,  # seq_len, coin_number (non-changeable)
                        activation='relu',
                        kernel_constraint=max_norm(maxi_norm)))  # maybe we can play with that number also

        model.add(Dropout(dropout))

        model.add(Reshape(target_shape=(1, self.dense_units,)))

        model.add(LSTM(
            units=self.inner_units,  # seq_len
            return_sequences=True))
        model.add(Dropout(dropout))

        model.add(LSTM(
            self.inner_units,  # lstm_units (changeable)
            return_sequences=False))
        model.add(Dropout(dropout))

        model.add(Dense(
            units=self.acion_size
        ))  # this can be changed too along with the first one
        model.add(Activation("softmax"))

        print(model.summary())
        return model

    def build_model_2reg(self):

        dropout_1 = self.dropout_1
        dropout_2 = self.dropout_2

        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2

        # Try adding regularization to the wieghts and activations so that the coins are less correlated
        # to one another and the predictions are more individualized
        model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

        #model.add(BatchNormalization(input_shape=(1,) + self.input_shape))

        model.add(Dense(self.dense_units,  # dense units (changeable)
                        input_shape=(1,) + self.input_shape,
                        activation='relu',
                        kernel_regularizer=regularizers.l2(l1),
                        activity_regularizer=regularizers.l1(l2),
                        kernel_constraint=max_norm(maxi_norm)))

        model.add(Dropout(dropout_2))
        #model.add(BatchNormalization())

        model.add(Reshape(target_shape=(1, self.dense_units,)))

        model.add(LSTM(
            input_shape=(1,) + self.input_shape,
            units=self.inner_units,  # seq_len
            return_sequences=True))
        model.add(Dropout(dropout_1))

        #model.add(BatchNormalization())

        model.add(LSTM(
            self.inner_units,  # lstm_units (changeable)
            return_sequences=False))
        model.add(Dropout(dropout_2))

        model.add(Dense(
            units=self.acion_size
        ))
        model.add(Activation("softmax"))

        print(model.summary())
        return model

    def build_model_cnn(self):

        dropout_1 = self.dropout_1
        dropout_2 = self.dropout_2

        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        kernel_size = self.kernel_size
        pooling_size = self.pooling_size
        max_bias = 2

        model = Sequential()
        model.add(Dense(self.dense_units,
                        input_shape=(1, ) + self.input_shape,
                        activation='elu'))
        #model.add(BatchNormalization(input_shape=(1,) + self.input_shape))

        model.add(Reshape(target_shape=(1, self.dense_units,)))

        model.add(Conv1D(self.inner_units,
                         kernel_size=kernel_size,
                         activation='elu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias)))
        model.add(MaxPooling1D(pool_size=pooling_size))
        model.add(Dropout(dropout_1))
        #model.add(BatchNormalization())

        model.add(Conv1D(self.inner_units,
                         kernel_size=kernel_size,
                         activation='elu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias)))
        model.add(MaxPooling1D(pool_size=pooling_size))
        model.add(Dropout(dropout_2))
        #model.add(BatchNormalization())
        model.add(Flatten())

        model.add(Dense(self.acion_size))

        model.add(Activation("softmax"))
        print(model.summary())

        return model

    def build_model_yang(self):

        dropout_1 = self.dropout_1
        dropout_2 = self.dropout_2

        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        max_bias = 2
        size = self.size  # The inner unit count of layers is different here to mimic the paper, which works
        # with size = 1

        model = Sequential()
        model.add(Dense(self.dense_units,
                        input_shape=(1, ) + self.input_shape,
                        activation='elu'))
        #  model.add(BatchNormalization(input_shape=(1,) + self.input_shape))
        # batchnormalization doesn't do anything, but like this i can output the model summary

        model.add(Reshape(target_shape=(1, self.dense_units,)))

        model.add(Conv1D(int(50 * size),
                         kernel_size=self.kernel_size,
                         activation='relu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias)))
        model.add(MaxPooling1D(pool_size=self.pooling_size))
        model.add(Dropout(dropout_2))
        #model.add(BatchNormalization())

        model.add(Conv1D(int(40 * size),
                         kernel_size=self.kernel_size,
                         activation='relu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias)))
        model.add(MaxPooling1D(pool_size=self.pooling_size))
        model.add(Dropout(dropout_1))
        #model.add(BatchNormalization())

        model.add(Conv1D(int(20 * size),
                         kernel_size=self.kernel_size,
                         activation='relu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(1,) + self.input_shape))
        model.add(MaxPooling1D(pool_size=self.pooling_size))
        model.add(Dropout(dropout_2))
        #model.add(BatchNormalization())

        model.add(Flatten())
        model.add(Dense(self.acion_size))

        model.add(Activation("softmax"))

        print(model.summary())
        return model

    def build_model_abe(self):
        # https://arxiv.org/ftp/arxiv/papers/1801/1801.01777.pdf

        dropout_1 = self.dropout_1
        dropout_2 = self.dropout_2

        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        max_bias = 2
        size = self.size  # The inner unit count of layers is different here to mimic the paper, which works
        # with size = 1

        model = Sequential()
        model.add(Dense(self.dense_units,
                        input_shape=(1,) + self.input_shape,
                        activation='elu'))
        # model.add(BatchNormalization(input_shape=(1,) + self.input_shape))

        model.add(Reshape(target_shape=(1, self.dense_units,)))

        model.add(Conv1D(int(100 * size),
                         kernel_size=1,
                         activation='tanh',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(1,) + self.input_shape
                         ))
        model.add(MaxPooling1D(pool_size=1))
        model.add(Dropout(dropout_2))
        model.add(BatchNormalization())

        model.add(Conv1D(int(50 * size),
                         kernel_size=1,
                         activation='tanh',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(1,) + self.input_shape
                         ))
        model.add(MaxPooling1D(pool_size=1))
        model.add(Dropout(dropout_1))
        #model.add(BatchNormalization())

        model.add(Conv1D(int(10 * size),
                         kernel_size=1,
                         activation='tanh',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(1,) + self.input_shape
                         ))
        model.add(MaxPooling1D(pool_size=1))
        model.add(Dropout(dropout_2))
        #model.add(BatchNormalization())

        model.add(Flatten())
        model.add(Dense(self.acion_size))
        model.add(Activation("softmax"))

        print(model.summary())
        return model

    def build_model_baseline(self):

        dropout = self.dropout
        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        max_bias = 2

        model = Sequential()

        model.add(Dense(units=self.dense_units,
                        input_shape=(1,) + self.input_shape,
                        kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                        kernel_constraint=max_norm(maxi_norm),
                        bias_constraint=max_norm(max_bias),
                        activation='relu'))
        model.add(Dropout(dropout))
        #model.add(BatchNormalization())
        model.add(Flatten())

        model.add(Dense(units=self.acion_size,
                        kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                        kernel_constraint=max_norm(maxi_norm),
                        bias_constraint=max_norm(max_bias)
                        ))

        model.add(Activation("softmax"))
        print(model.summary())
        return model
