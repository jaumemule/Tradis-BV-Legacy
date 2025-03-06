import lstm
import continuous_functions as cf
import functions
import time
import sys
import os
import random
from datetime import datetime
import numpy as np
from tensorflow import set_random_seed
from keras.callbacks import Callback, LearningRateScheduler
from sklearn.externals import joblib
import warnings

random.seed(1102)  # ensuring reproducibility
np.random.seed(1102)  # same
set_random_seed(1102)  # yes, python sucks

epochs  = int(sys.argv[1])  # input the epochs from command line (for model testing purposes only)

unix = False  # if you are using a unix system, else set to False

# specify the model you want to run:
# options are: 1, 2, "2reg", 3, 4, "chinese"
which_model = "chinese"

# parameters
# these parameters need to be adjusted to optimize the model
seq_len = 100            # this is the amount of data (in minutes) used for the forecast
forecast_len = 1       # this is the forecast time in minutes
dense_units = 128       # this number needs to be played with (last best = 128)
lstm_units = 64 * 2     # ídem (last best = 64)
dropout = 0.1           # also (last best = 0.1)
learning_rate = 0.001   # (last best = 0.0001)
batch_size = 256*8        # try to optimize GPU capabilities
interval = 1

# other parameters

train_days = 18         # deprecated
pred_days = 14

amount = 100
fee = 0.0014 * 2
p1 = 0.4    # This controls how much money is invested in each prediction,
p2 = 0.3    # so the investment on coin 1 will be amount * p1
p3 = 0.2    # It's technically not required but obviously they should add up to one
p4 = 0.1    # you can add as many percentages as you want, just make sure to add them
p5 = 0.     # also in the dictionary below

      ###################################
###### Do not touch beyond this point!!! ######
      ###################################

# Packing parameters into dictionaries to make funcions more legible:

percentages = {"p1": p1,
               "p2": p2,
               "p3": p3,
               "p4": p4,
               "p5": p5}


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

lrate = LearningRateScheduler(lambda x:  learning_rate / (1. + 0), verbose=1)
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

    # Load data and filter by coins that we can trade to BNB
    pre_df = functions.data_load("data_hourly.csv", range(4000))
    df = functions.filter_coins(pre_df)

    # df = df.iloc[::2,:]

    number_of_coins = int(df.shape[0]/2)

    # The "number" is the amount of trainig data that we will be using, in minutes
    # It can be chosen either by choosing it directly or by choosing the number of
    # days that will be predicted.

    # number = train_days * 24
    number = df.shape[1] - 24 * pred_days # We predict only the last n days

    parameters["number"] = number # add it to the dictionary

    print("Model trained on " + str(df.shape[0]/2) + " coins during " + str(round(number/24, 1)) + " days.")

    # X_train, y_train, scaler = cf.train(df, parameters)
    # This function reshapes the input dataframe into usable training data

    X_train, y_train, scaler = cf.train_rand(df, parameters)

    joblib.dump(scaler, 'scaler_hourly.save')

    dims = [X_train.shape[2], seq_len, dense_units, lstm_units]

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

    history = model.fit(
        X_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=0.2,
        callbacks=[lrate, functions.er])

    model.save('fast_model_hourly.h5')  # we save the model

    print("Starting predictions over " + str(pred_days) + " days every " + str(forecast_len) + " hours.")

    # In the following three lines we create the log
    name_time = datetime.fromtimestamp(start_time).strftime("%A, %B %d, %Y %I:%M:%S")
    name_time = functions.get_valid_filename(name_time)  # format for windows

    if unix:
        file = open("logs/log_" + str(name_time) + ".txt","w")  # makeshift log -> needs to be improved
    else:
        file = open("logs\\log_" + str(name_time) + ".txt","w")  # makeshift log -> needs to be improved

    cf.write_log(file, parameters, name_time, start_time)   # writes the different parameters into the log

    # This loop takes the pedictions at every epoch in the form of the five coins
    # with the highest prediction and plots the return at every timestep of
    # an inicial investment of "amount". Finally, it also stores these returns in the log.

    coins_historical = cf.coins_new(df, parameters, scaler, model, number_of_coins)
    amount_historical, final_amount = cf.investment(coins_historical, df, parameters, percentages)
    cf.plot_investment(amount_historical, df, name_time, final_amount, parameters)
    cf.print_investment(coins_historical, amount_historical, epochs, parameters)
    file.write("\nReturn amount for epoch " + str(epochs) + " is " + str(final_amount))

    file.close()

    #plt.show() # Show the plots computed in the previous loop

    cf.plot_loss(history, parameters) # we plot loss and validation loss
