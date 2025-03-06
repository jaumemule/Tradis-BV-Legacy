import lstm
import continuous_functions as cf
import functions
import time
import sys
import os
import random
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tensorflow import set_random_seed
from keras.callbacks import Callback, LearningRateScheduler, EarlyStopping
from sklearn.externals import joblib

random.seed(1102) # ensuring reproducibility
np.random.seed(1102) # same
set_random_seed(1102) # yes, python sucks

epochs  = int(sys.argv[1]) # input the epochs from command line (for model testing purposes only)

# using unix or windows, change to False if using Windows.
unix = False

# specify the model you want to run:
# options are: 1, 2, "2reg", 3, 4, "chinese"
which_model = 2

# parameters
# these parameters need to be adjusted to optimize the model
seq_len = 180            # this is the amount of data (in minutes) used for the forecast
forecast_len = 60       # this is the forecast time in minutes
dense_units = 128       # this number needs to be played with (last best = 128)
lstm_units = 64 * 2     # ídem (last best = 64)
dropout = 0.2           # also (last best = 0.2)
learning_rate = 0.001   # (last best = 0.0001)
batch_size = 128        # quite optimal
interval = 4            # explanation in following text:

"""
The way training data is generated is the following: we take all historical
data and store it in df. This is then a dataframe with dimensions
number_of_coins * 2 x minutes (the times 2 comes from storing price and volume)
For each trading index that we compute we add one number of coins, so, if we
are using two indices, we have:

                [number_of_coins * 4 x minutes]

We then pick "training_number" of minutes and use it for prediction, so that df
has number_of_coins * 4 x training_number shape. From this, we create training
data the following way: we pick every "interval" number of minutes and create
a training observation of shape number_of_coins * 4 x seq_len together with a target
observation of shape number_of_coins * 4 x 1 consisting of the observation
"forecast_len" away from the last minute of the training data. We store all
these training data in a numpy array (X_test) with shape:

        [minutes/interval x seq_len x number_of_coins * 4]

together with the target data with shape:

        [minutes/interval x number_of_coins * 4 x 1]

Test data is treated the same but with interval = 1.

Note: minutes/interval sizes are not exact because we have to account for
data for which we don't have enough historical and stuff like that, so it has
minor corrections in the functions.
"""
# trading indices

# rsi
rsi_length = 14     # in days
rsi_gap = 24         # in hours

# stoch
stoch_length = 14   # in days

# other parameters

train_days = 18         # either this one or the one below will be used
pred_days = 7

amount = 100      # initial trading amount
fee = 0.0014 * 2   # simulated fee from trader
p1 = 0.4    # This controls how much money is invested in each prediction,
p2 = 0.3    # so the investment on coin 1 will be amount * p1
p3 = 0.2    # It's technically not required but obviously they should add up to one
p4 = 0.1    # you can add as many percentages as you want, just make sure to add them
p5 = 0.     # also in the dictionary below

      ###################################
###### Do not touch beyond this point!!! ######
      ###################################

# Packing parameters into dictionaries to make funcions more legible:

percentages = {"p1" : p1,
               "p2" : p2,
               "p3" : p3,
               "p4" : p4,
               "p5" : p5}


parameters = {"seq_len": seq_len,
              "forecast_len": forecast_len,
              "dense_units": dense_units,
              "lstm_units": lstm_units,
              "dropout": dropout,
              "learning_rate": learning_rate,
              "batch_size": batch_size,
              "pred_days": pred_days,
              "train_days": train_days,
              "amount": amount,
              "fee": fee,
              "interval": interval,
              "unix": unix}


class prediction_history(Callback):
    # This class is used to store the precictions (in form of predicted best coins)
    # for every epoch for testing purposes
    # more options and info on https://keras.io/callbacks/
    # Results often vary wildly upon epochs and this is an attempt at checking
    # for patterns
    # TODO: Add logs

    def __init__(self):
        self.predhis = []
    def on_epoch_end(self, epoch, logs={}):
        coins_historical = cf.coins_new(df, parameters, scaler, model, number_of_coins)
        # The previous line contains the actual predictions and converts them
        # into the 5 best valued coins
        self.predhis.append(coins_historical)

er = EarlyStopping(monitor='val_loss',
                   min_delta=0.0001,
                   patience=0,
                   verbose=1,
                   mode='auto')

lrate = LearningRateScheduler(lambda x:  learning_rate / (1. + 0), verbose = 1)
# this function lowers the learning rate at each epoch, it's part of the
# keras callbacks.

if __name__=='__main__':
# This is the main run function

    # create directories if they don't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if not os.path.exists("charts"):
        os.makedirs("charts")
    if not os.path.exists("investments"):
        os.makedirs("investments")

    start_time = time.time()

    print('> Loading data... ')

    # Load data and filter by coins that we can trade to BNB (so, coins that
    # we can trade at binance, the trader we arer using right now), in the future
    # this might change

    # 126017
    pre_df = functions.data_load("new_data_4.csv", range(126017))
    # range included in case you don't want to load the whole file (for testing
    # and memory saving purposes)
    df = functions.filter_coins(pre_df)
    number_of_coins = int(df.shape[0]/2)
    # we are checking coin price and 24h
    # volume, so that there are two values for each coin

    # compute rsi and add it to df
    #rsi = functions.compute_rsi(df, length = rsi_length, gap = rsi_gap)
    #stoch = functions.compute_stoch(df, length = stoch_length)
    #df = pd.concat([df,rsi,stoch])
    #df.fillna(method = "pad", inplace = True)


    # we need to remove the values that are too early to be able to computed
    # the indices (i.e., there is not enough historical data)
    # this can be safely removed for testing if the the amount of data needed is
    # too high
    #leftover = max(rsi_length, stoch_length) * 24*60
    #df = df.iloc[:,leftover:]


    # The "training_number" is the amount of trainig data that we will be using, in minutes
    # It can be selected either by choosing it directly or by choosing the number of
    # days that will be predicted.

    #number = train_days * 24 * 60 # Choose this one or the one below
    training_number = df.shape[1] - 60 * 24 * pred_days # We predict only the last n days

    parameters["number"] = training_number # add it to the dictionary

    print("> Training model on " + str(int(df.shape[0]/4)) + " coins during " + str(round(training_number/60/24, 1)) + " days...")

    # This function reshapes the input dataframe into usable training data
    # There are two options, train data as it is or also shuffle it.
    # TO-DO: check which is best.
    #X_train, y_train, scaler = cf.train(df, parameters)
    X_train, y_train, scaler = cf.train_rand(df, parameters)

    joblib.dump(scaler, 'scaler.save')
    # save the scaler for the predictor (in the director directory)

    predictions = prediction_history()
    # Initialization of the predictions at every epoch

    dims = [X_train.shape[2], seq_len, dense_units, lstm_units]
    # LSTM parameters

    # The following are different models that we should try; they are stored
    # at lstm.py. They increase in difficulty except for the "chinese", that
    # comes from a paper linked in the file.

    if which_model == 1:
        model = lstm.build_model1(dims, dropout, learning_rate)
    elif which_model == 2:
        model = lstm.build_model2(dims, dropout, learning_rate)
    elif which_model == "2reg":
        model = lstm.build_model2_reg(dims, dropout, learning_rate)
    elif which_model == 3:
        model = lstm.build_model3(dims, dropout, learning_rate)
    elif which_model == 4:
        model = lstm.build_model4(dims, dropout, learning_rate)
    elif which_model == "chinese":
        model = lstm.build_model_chinese(dims, dropout, learning_rate)
    else:
        model = lstm.build_model2_stateful(dims, dropout, learning_rate, batch_size) # currently not working
    # Loading the model from the lstm.py file
    # Note: change the logs if you change the model!
    # TODO: do this automatically

    history = model.fit(
        X_train,
        y_train,
        batch_size = batch_size,
        epochs = epochs,
        validation_split = 0.2,
        callbacks = [predictions, lrate, er])

    model.save('model.h5')
    # save the weights to be used in the director

    print("> Starting predictions over " + str(pred_days) + " days every " + str(forecast_len) + " minutes...")

    # In the following three lines we create the log
    name_time = datetime.fromtimestamp(start_time).strftime("%A, %B %d, %Y %I:%M:%S")

    if unix:
        file = open("logs/log_" + str(name_time) + ".txt","w")  # makeshift log -> needs to be improved
    else:
        file = open("logs\\log_" + str(name_time[:8]) + ".txt","w")  # makeshift log -> needs to be improved

    cf.write_log(file, parameters, name_time, start_time)   # writes the different parameters into the log

    # This loop takes the pedictions at every epoch in the form of the five coins
    # with the highest prediction and plots the return at every timestep of
    # an inicial investment of "amount". Finally, it also stores these returns in the log.
    for i in range(len(predictions.predhis)):
        coins_historical = predictions.predhis[i] # Get the predictions at every epoch
        amount_historical, final_amount = cf.investment(coins_historical, df, parameters, percentages)
        cf.plot_investment(amount_historical, df, i, final_amount, parameters)
        cf.print_investment(coins_historical, amount_historical, i, parameters)
        file.write("\nReturn amount for epoch " + str(i + 1) + " is " + str(final_amount))

    file.close()

    cf.plot_loss(history, parameters) # we plot loss and validation loss
