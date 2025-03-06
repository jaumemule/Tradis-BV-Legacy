import time
import keras
from keras.layers import Input
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.models import Sequential, Model
from keras import optimizers
from keras import regularizers
from keras.constraints import max_norm
import tensorflow as tf

#### Models ####

# current favourite model is 2 (non-regularized)

# original and working model

# model
def build_model1(dims, dropout, learning_rate):
    model = Sequential()

    model.add(LSTM(
        input_shape=(dims[1], dims[0]),
        units=dims[1],
        return_sequences=True))
    model.add(Dropout(dropout))

    model.add(LSTM(
        dims[3],
        return_sequences=False))
    model.add(Dropout(dropout))

    model.add(Dense(
        units=dims[0]))
    model.add(Activation("linear"))

    start = time.time()

    # All parameter gradients will be clipped to
    # a maximum norm of 1.
    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model


# second model, with a fully connected layer before the lstm
# takes quite a while to train
# remember: dims = [X_train.shape[2], seq_len, dense_units, lstm_units]

def build_model2(dims, dropout, learning_rate):
    model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[0]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(LSTM(
        input_shape=(dims[1], dims[2]), # seq_len, dense units
        units=dims[1], # seq_len
        return_sequences=True))
    model.add(Dropout(dropout))

    model.add(LSTM(
        dims[3], # lstm_units (changeable)
        return_sequences=False))
    model.add(Dropout(dropout))

    model.add(Dense(
        units=dims[0], # again, coin_number for the output
        activation = 'linear',
        kernel_constraint=max_norm(2.))) # this can be changed too along with the first one

    start = time.time()


    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)
    #adagrad = optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model

def build_model2_stateful(dims, dropout, learning_rate, batch_size):
    dims[1] = dims[1] - dims[1]%batch_size
    model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[0]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also


    model.add(Dropout(dropout))

    model.add(LSTM(
        batch_input_shape=(batch_size,dims[1],dims[2]), # seq_len, dense units
        units=dims[1], # seq_len
        return_sequences=True,
        stateful = True))
    model.add(Dropout(dropout))

    model.add(LSTM(
        dims[3], # lstm_units (changeable)
        return_sequences=False,
        stateful = True))
    model.add(Dropout(dropout))

    model.add(Dense(
        output_dim= dims[0], # again, coin_number for the output
        activation = 'linear',
        kernel_constraint=max_norm(2.))) # this can be changed too along with the first one

    start = time.time()


    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)
    #adagrad = optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model

def build_model2_reg(dims, dropout, learning_rate):
    # Try adding regularization to the wieghts and activations so that the coins are less correlated
    # to one another and the predictions are more individualized
    model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[0]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_regularizer=regularizers.l2(0.01),
                    activity_regularizer=regularizers.l1(0.01)))
                    # kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(LSTM(
        input_shape=(dims[1], dims[2]), # seq_len, dense units
        units=dims[1], # seq_len
        return_sequences=True))
    model.add(Dropout(dropout))

    model.add(LSTM(
        dims[3], # lstm_units (changeable)
        return_sequences=False))
    model.add(Dropout(dropout))

    model.add(Dense(
        units=dims[0], # again, coin_number for the output
        activation = 'linear',
        kernel_constraint=max_norm(2.))) # this can be changed too along with the first one

    start = time.time()

    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)
    #adagrad = optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model


# intentem incloure valors en l'últim layer:

def build_model2_reg_inputed(dims, dropout, learning_rate, input_shape):
    # Try adding regularization to the wieghts and activations so that the coins are less correlated
    # to one another and the predictions are more individualized
    # model = Sequential()

    main_input = Input(shape=(dims[1], dims[0]), name='main_input')

    x = Dense(dims[2], activation='relu',
              kernel_regularizer=regularizers.l2(0.01),
              activity_regularizer=regularizers.l1(0.01))(main_input)

    x = Dropout(dropout)(x)

    x = LSTM(units=dims[3],  # seq_len
             return_sequences=True)(x)

    x = Dropout(dropout)(x)

    x = LSTM(dims[3],  # lstm_units (changeable)
             return_sequences=False)(x)

    lstm_out = Dropout(dropout)(x)

    auxiliary_output = Dense(dims[0], activation='sigmoid', name='aux_output')(lstm_out)

    auxiliary_input = Input(shape=(input_shape,), name='auxiliary_input')  # We enter the auxiliary input here
    x_aux = Dense(32, activation='relu')(auxiliary_input)
    x_aux = Dense(32, activation='relu')(x_aux)

    x = keras.layers.concatenate([lstm_out, x_aux])

    x = Dense(dims[2], activation='linear', kernel_constraint=max_norm(2.))(x)
    main_output = Dense(dims[0], activation='linear', name='main_output', kernel_constraint=max_norm(2.))(x)

    model = Model(inputs=[main_input, auxiliary_input], outputs=[main_output])

    start = time.time()

    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)
    # adagrad = optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)

    return model

# third model, with a second fully connected layer before the lstm

def build_model3(dims, dropout, learning_rate):
    model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[0]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[2]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))


    model.add(LSTM(
        input_shape=(dims[1], dims[2]), # seq_len, dense units
        units=dims[1], # seq_len
        return_sequences=True))
    model.add(Dropout(dropout))

    model.add(LSTM(
        dims[3], # lstm_units (changeable)
        return_sequences=False))
    model.add(Dropout(dropout))

    model.add(Dense(
        units=dims[0], # again, coin_number for the output
        activation = 'linear',
        kernel_constraint=max_norm(2.))) # this can be changed too along with the first one

    start = time.time()


    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model

# fourth model, with four fully connected layers before the lstm

def build_model4(dims, dropout, learning_rate):
    model = Sequential()

        # All parameter gradients will be clipped to
        # a maximum norm of 2.

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[0]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[2]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[2]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(Dense(dims[2], # dense units (changeable)
                    input_shape=(dims[1],dims[2]), # seq_len, coin_number (non-changeable)
                    activation='relu',
                    kernel_constraint=max_norm(2.))) # maybe we can play with that number also

    model.add(Dropout(dropout))

    model.add(LSTM(
        input_shape=(dims[1], dims[2]), # seq_len, dense units
        units=dims[1], # seq_len
        return_sequences=True))
    model.add(Dropout(dropout))

    model.add(LSTM(
        dims[3], # lstm_units (changeable)
        return_sequences=False))
    model.add(Dropout(dropout))

    model.add(Dense(
        units=dims[0], # again, coin_number for the output
        activation = 'linear',
        kernel_constraint=max_norm(2.))) # this can be changed too along with the first one

    start = time.time()


    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model

def build_model_chinese(dims, dropout, learning_rate):
    # model based on the following paper:
    # http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7364089

    model = Sequential()

    model.add(LSTM(
        input_shape=(dims[1], dims[0]), # seq_len, dense units
        units=dims[1], # seq_len
        return_sequences=True))

    model.add(LSTM(
        units= dims[3], # seq_len
        return_sequences=True))


    model.add(LSTM(
        units = dims[3], # lstm_units (changeable)
        return_sequences=False))
    #model.add(Dropout(dropout))

    model.add(Dense(
        units= dims[0], # again, coin_number for the output
        activation = 'linear',
        kernel_constraint=max_norm(2.))) # this can be changed too along with the first one

    start = time.time()


    adam = optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999)

    model.compile(loss="mse", optimizer=adam)
    print("> Compilation Time : ", time.time() - start)
    return model
