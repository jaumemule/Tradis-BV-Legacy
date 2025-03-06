import time
from keras.layers.core import Dense, Activation, Dropout
from keras.layers import Conv1D, Flatten, MaxPooling1D, AveragePooling2D, Input, Conv2D, add
from keras.layers.recurrent import LSTM
from keras.models import Sequential, Model
from keras import optimizers
from keras import regularizers
from keras.constraints import max_norm
from keras.layers.normalization import BatchNormalization


class ModelWrapper(object):

    def __init__(self, training_observations, coin_number, cfg):

        self.seq_len = cfg['training']['seq_len']
        self.inner_units = cfg['net']['inner_units']
        self.dense_units = cfg['net']['dense_units']
        self.size = cfg['net']['size']
        self.training_obs = training_observations
        self.coin_number = coin_number
        self.learning_rate = cfg["net"]["learning_rate"]
        self.dropout = cfg["net"]["dropout"]
        self.name = ""
        self.which = cfg["training"]["which_model"]
        self.kernel_size = cfg['net']['kernel_size']
        self.pooling_size = cfg['net']['pooling_size']
        self.l1 = cfg['net']['l1']
        self.l2 = cfg['net']['l2']
        self.maxi_norm = cfg['net']['max_norm']
        print("Building model " + str(self.which))

    def build_model_(self, model_type='linear', input_shape=None):
        which = self.which

        if which == 1:
            return self.build_model_1()

        elif which == 2:
            return self.build_model_2()

        elif which == "lstm":
            return self.build_model_2reg()

        elif which == "cnn":
            return self.build_model_cnn(model_type)

        elif which == "yang":
            return self.build_model_yang(model_type)

        elif which == "baseline":
            return self.build_model_baseline(model_type)

        elif which == "abe":
            return self.build_model_abe(model_type)

        elif which == "resnet":  # TODO: not working, work on it
            return self.build_model_resnet(input_shape)

        else:
            # FIXME: I'm reusing the closest error I could find, this needs to be changed
            raise ModuleNotFoundError("Model doesn't exist. Exiting.")

    def build_model_1(self):

        dropout = self.dropout
        model = Sequential()

        model.add(LSTM(
            input_shape=(self.seq_len, self.training_obs),
            units=self.inner_units,
            return_sequences=True))
        model.add(Dropout(dropout))

        model.add(LSTM(
            self.inner_units,
            return_sequences=False))
        model.add(Dropout(dropout))

        model.add(Dense(
            units=self.coin_number))
        model.add(Activation("linear"))

        start = time.time()

        # All parameter gradients will be clipped to
        # a maximum norm of 1.
        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)

        model.compile(loss="mse", optimizer=adam)
        print("> Compilation Time : ", time.time() - start)
        return model
    
    def build_model_2(self):

        dropout = self.dropout
        maxi_norm = self.maxi_norm

        model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

        model.add(Dense(units=self.dense_units,  # dense units (changeable)
                        input_shape=(self.seq_len, self.training_obs),  # seq_len, coin_number (non-changeable)
                        activation='relu',
                        kernel_constraint=max_norm(maxi_norm)))  # maybe we can play with that number also

        model.add(Dropout(dropout))

        model.add(LSTM(
            input_shape=(self.seq_len, self.dense_units),  # seq_len, dense units
            units=self.inner_units,  # seq_len
            return_sequences=True))
        model.add(Dropout(dropout))

        model.add(LSTM(
            self.inner_units,  # lstm_units (changeable)
            return_sequences=False))
        model.add(Dropout(dropout))

        model.add(Dense(
            units=self.coin_number
        ))  # this can be changed too along with the first one
        model.add(Activation("linear"))

        start = time.time()

        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)
        # adagrad = optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)

        model.compile(loss="mse", optimizer=adam)
        print("> Compilation Time : ", time.time() - start)
        return model
    
    def build_model_2reg(self):

        dropout = self.dropout
        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2

        # Try adding regularization to the wieghts and activations so that the coins are less correlated
        # to one another and the predictions are more individualized
        model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

        model.add(BatchNormalization())

        model.add(Dense(self.dense_units,  # dense units (changeable)
                        input_shape=(self.seq_len,self.training_obs),
                        activation='relu',
                        kernel_regularizer=regularizers.l2(l1),
                        activity_regularizer=regularizers.l1(l2),
                        kernel_constraint=max_norm(maxi_norm)))

        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(LSTM(
            input_shape=(self.seq_len, self.dense_units),  # seq_len, dense units
            units=self.inner_units,  # seq_len
            return_sequences=True))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(LSTM(
            self.inner_units,  # lstm_units (changeable)
            return_sequences=False))
        model.add(Dropout(dropout))

        model.add(Dense(
            units=self.coin_number
            ))
        model.add(Activation("linear"))

        start = time.time()

        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)
        # adagrad = optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)

        model.compile(loss="mse", optimizer=adam)
        print("> Compilation Time : ", time.time() - start)
        return model

    def build_model_cnn(self, model_type):

        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)
        dropout = self.dropout
        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        kernel_size = self.kernel_size
        pooling_size = self.pooling_size
        max_bias = 2

        model = Sequential()
        #model.add(Dense(dims[2], activation='elu'))
        model.add(BatchNormalization())

        model.add(Conv1D(self.inner_units,
                         kernel_size=kernel_size,
                         activation='elu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=pooling_size))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Conv1D(self.inner_units,
                         kernel_size=kernel_size,
                         activation='elu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=pooling_size))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())
        model.add(Flatten())

        model.add(Dense(self.coin_number))

        if model_type == 'linear':
            model.add(Activation("linear"))
            model.compile(loss="mse", optimizer=adam)
        else:
            model.add(Activation("sigmoid"))
            model.compile(loss="binary_crossentropy", optimizer=adam, metrics=['accuracy'])

        return model

    def build_model_yang(self, model_type):

        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)
        dropout = self.dropout
        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        max_bias = 2
        size = self.size  # The inner unit count of layers is different here to mimic the paper, which works
                  # with size = 1

        model = Sequential()
        # model.add(Dense(dims[2], activation='elu'))
        model.add(BatchNormalization())

        model.add(Conv1D(int(50*size),
                         kernel_size=5,
                         activation='relu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Conv1D(int(40*size),
                         kernel_size=5,
                         activation='relu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Conv1D(int(20*size),
                         kernel_size=3,
                         activation='relu',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Flatten())
        model.add(Dense(self.coin_number))

        if model_type == 'linear':
            model.add(Activation("linear"))
            model.compile(loss="mse", optimizer=adam)
        else:
            model.add(Activation("sigmoid"))
            model.compile(loss="binary_crossentropy", optimizer=adam, metrics=['accuracy'])

        return model

    def build_model_abe(self, model_type):
        # https://arxiv.org/ftp/arxiv/papers/1801/1801.01777.pdf

        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)
        dropout = self.dropout
        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        max_bias = 2
        size = self.size  # The inner unit count of layers is different here to mimic the paper, which works
                  # with size = 1

        model = Sequential()
        # model.add(Dense(dims[2], activation='elu'))
        model.add(BatchNormalization())

        model.add(Conv1D(int(100*size),
                         kernel_size=5,
                         activation='tanh',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Conv1D(int(50*size),
                         kernel_size=5,
                         activation='tanh',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Conv1D(int(10*size),
                         kernel_size=3,
                         activation='tanh',
                         kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                         kernel_constraint=max_norm(maxi_norm),
                         bias_constraint=max_norm(max_bias),
                         input_shape=(self.seq_len, self.training_obs)))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

        model.add(Flatten())

        model.add(Dense(self.coin_number))
        model.add(Activation("sigmoid"))

        if model_type == 'linear':
            model.add(Activation("linear"))
            model.compile(loss="mse", optimizer=adam)
        else:
            model.add(Activation("sigmoid"))
            model.compile(loss="binary_crossentropy", optimizer=adam, metrics=['accuracy'])

        return model

    def build_model_baseline(self, model_type):

        adam = optimizers.Adam(lr=self.learning_rate, beta_1=0.9, beta_2=0.999)
        dropout = self.dropout
        maxi_norm = self.maxi_norm
        l1 = self.l1
        l2 = self.l2
        max_bias = 2

        model = Sequential()
        model.add(BatchNormalization())
        model.add(Dense(units=self.dense_units,
                        input_shape=(self.seq_len, self.training_obs),
                        kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                        kernel_constraint=max_norm(maxi_norm),
                        bias_constraint=max_norm(max_bias),
                        activation='relu'))
        model.add(Dropout(dropout))
        model.add(BatchNormalization())
        model.add(Flatten())

        model.add(Dense(units=self.coin_number,
                        kernel_regularizer=regularizers.l1_l2(l1=l1, l2=l2),
                        kernel_constraint=max_norm(maxi_norm),
                        bias_constraint=max_norm(max_bias)
                        ))

        if model_type == 'linear':
            model.add(Activation("linear"))
            model.compile(loss="mse", optimizer=adam)
        else:
            model.add(Activation("sigmoid"))
            model.compile(loss="binary_crossentropy", optimizer=adam, metrics=['accuracy'])

        return model

    # Model version
    # Orig paper: version = 1 (ResNet v1), Improved ResNet: version = 2 (ResNet v2)

    def build_model_resnet(self, input_shape):
        version = 1
        n = 3

        # Computed depth from supplied model parameter n
        if version == 1:
            depth = n * 6 + 2
        elif version == 2:
            depth = n * 9 + 2

        # Model name, depth and version
        model_type = 'ResNet%dv%d' % (depth, version)

        def lr_schedule(epoch):
            """Learning Rate Schedule

            Learning rate is scheduled to be reduced after 80, 120, 160, 180 epochs.
            Called automatically every epoch as part of callbacks during training.

            # Arguments
                epoch (int): The number of epochs

            # Returns
                lr (float32): learning rate
            """
            lr = 1e-3
            if epoch > 180:
                lr *= 0.5e-3
            elif epoch > 160:
                lr *= 1e-3
            elif epoch > 120:
                lr *= 1e-2
            elif epoch > 80:
                lr *= 1e-1
            print('Learning rate: ', lr)
            return lr

        def resnet_layer(inputs,
                         num_filters=16,
                         kernel_size=3,
                         strides=1,
                         activation='relu',
                         batch_normalization=True,
                         conv_first=True):
            """2D Convolution-Batch Normalization-Activation stack builder

            # Arguments
                inputs (tensor): input tensor from input image or previous layer
                num_filters (int): Conv2D number of filters
                kernel_size (int): Conv2D square kernel dimensions
                strides (int): Conv2D square stride dimensions
                activation (string): activation name
                batch_normalization (bool): whether to include batch normalization
                conv_first (bool): conv-bn-activation (True) or
                    bn-activation-conv (False)

            # Returns
                x (tensor): tensor as input to the next layer
            """
            conv = Conv2D(num_filters,
                          kernel_size=kernel_size,
                          strides=strides,
                          padding='same',
                          kernel_initializer='he_normal',
                          kernel_regularizer=regularizers.l2(1e-4))

            x = inputs
            if conv_first:
                x = conv(x)
                if batch_normalization:
                    x = BatchNormalization()(x)
                if activation is not None:
                    x = Activation(activation)(x)
            else:
                if batch_normalization:
                    x = BatchNormalization()(x)
                if activation is not None:
                    x = Activation(activation)(x)
                x = conv(x)
            return x

        def resnet_v1(input_shape, depth, num_classes=10):
            """ResNet Version 1 Model builder [a]

            Stacks of 2 x (3 x 3) Conv2D-BN-ReLU
            Last ReLU is after the shortcut connection.
            At the beginning of each stage, the feature map size is halved (downsampled)
            by a convolutional layer with strides=2, while the number of filters is
            doubled. Within each stage, the layers have the same number filters and the
            same number of filters.
            Features maps sizes:
            stage 0: 32x32, 16
            stage 1: 16x16, 32
            stage 2:  8x8,  64
            The Number of parameters is approx the same as Table 6 of [a]:
            ResNet20 0.27M
            ResNet32 0.46M
            ResNet44 0.66M
            ResNet56 0.85M
            ResNet110 1.7M

            # Arguments
                input_shape (tensor): shape of input image tensor
                depth (int): number of core convolutional layers
                num_classes (int): number of classes (CIFAR10 has 10)

            # Returns
                model (Model): Keras model instance
            """
            if (depth - 2) % 6 != 0:
                raise ValueError('depth should be 6n+2 (eg 20, 32, 44 in [a])')
            # Start model definition.
            num_filters = 16
            num_res_blocks = int((depth - 2) / 6)

            inputs = Input(shape=input_shape)
            size = 10
            x = Conv1D(int(20 * size),
                            kernel_size=3,
                            activation='relu'
                            )(inputs)
            print(x.shape)

            x = resnet_layer(inputs=x)
            # Instantiate the stack of residual units
            for stack in range(3):
                for res_block in range(num_res_blocks):
                    strides = 1
                    if stack > 0 and res_block == 0:  # first layer but not first stack
                        strides = 2  # downsample
                    y = resnet_layer(inputs=x,
                                     num_filters=num_filters,
                                     strides=strides)
                    y = resnet_layer(inputs=y,
                                     num_filters=num_filters,
                                     activation=None)
                    if stack > 0 and res_block == 0:  # first layer but not first stack
                        # linear projection residual shortcut connection to match
                        # changed dims
                        x = resnet_layer(inputs=x,
                                         num_filters=num_filters,
                                         kernel_size=1,
                                         strides=strides,
                                         activation=None,
                                         batch_normalization=False)
                    x = add([x, y])
                    x = Activation('relu')(x)
                num_filters *= 2

            # Add classifier on top.
            # v1 does not use BN after last shortcut connection-ReLU
            x = AveragePooling2D(pool_size=8)(x)
            y = Flatten()(x)
            outputs = Dense(num_classes,
                            activation='softmax',
                            kernel_initializer='he_normal')(y)

            # Instantiate model.
            model = Model(inputs=inputs, outputs=outputs)

            return model

        model = resnet_v1(input_shape=input_shape, depth=depth, num_classes=2)
        model.compile(loss='categorical_crossentropy',
                      optimizer=optimizers.Adam(lr=lr_schedule(0)),
                      metrics=['accuracy'])
        model.summary()
        print(model_type)

        return model
