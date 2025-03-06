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
from keras.callbacks import Callback, LearningRateScheduler
from sklearn.externals import joblib

random.seed(1102) # ensuring reproducibility
np.random.seed(1102) # same
set_random_seed(1102) # yes, python sucks

epochs  = int(sys.argv[1]) # input the epochs from command line (for model testing purposes only)

# specify the model you want to run:
# options are: 1, 2, "2reg", 3, 4, "chinese"
which_model = 2

# parameters
# these parameters need to be adjusted to optimize the model
seq_len = 200            # this is the amount of data (in minutes) used for the forecast
forecast_len = 2       # this is the forecast time in minutes
dense_units = 128*2       # this number needs to be played with (last best = 128)
lstm_units = 64 * 4     # ídem (last best = 64)
dropout = 0.5           # also (last best = 0.2)
learning_rate = 0.005   # (last best = 0.0001)
batch_size = 128*2        # quite optimal
interval = 1

# other parameters

train_days = 18         # deprected
pred_days = 5

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
              "interval": interval}


class prediction_history(Callback):
    # This class is used to store the precictions (in form of predicted best coins)
    # for every epoch for testing purposes
    # more options and info on https://keras.io/callbacks/
    # I should add logs

    def __init__(self):
        self.predhis = []
    def on_epoch_end(self, epoch, logs={}):
        coins_historical = cf.coins(df, parameters, scaler, model)
        # The previous line contains the actual predictions and converts them
        # into the 5 best valued coins
        self.predhis.append(coins_historical)

lrate = LearningRateScheduler(lambda x:  learning_rate / (1. + x), verbose = 1)
# this function lowers the learning rate at each epoch, it's part of the
# keras callbacks.

if __name__=='__main__':
# This is the main run function

    # create directories if they don't exists
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if not os.path.exists("charts"):
        os.makedirs("charts")
    if not os.path.exists("investments"):
        os.makedirs("investments")

    start_time = time.time()

    print('> Loading data... ')

    pre_df = functions.data_load("quarterly_data.csv")
    df = functions.filter_coins(pre_df)
    df = df[df.columns[::2]]

    # The "number" is the amount of trainig data that we will be using, in minutes
    # It can be chosen either by choosing it directly or by choosing the number of
    # days that will be predicted.

    #number = train_days * 24 * 60 # Choose this one or the one below
    number = df.shape[1] - 2 * 24 * pred_days # We predict only the last n days

    parameters["number"] = number # add it to the dictionary

    print("Model trained on " + str(df.shape[0]) + " coins during " + str(round(number/2/24, 1)) + " days.")

    #X_train, y_train, scaler = cf.train(df, parameters)
    # This function reshapes the input dataframe into usable training data

    X_train, y_train, scaler = cf.train_rand(df, parameters)
    joblib.dump(scaler, 'scaler_quarterly.save')

    predictions = prediction_history()
    # Initialization of the predictions at every epoch

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
        batch_size = batch_size,
        epochs = epochs,
        validation_split = 0.2,
        callbacks = [predictions, lrate])

    model.save('model_quarterly.h5') # save the weights, just in case

    print("Starting predictions over " + str(pred_days) + " days every " + str(forecast_len) + " minutes.")


    # In the following three lines we create the log
    name_time = datetime.fromtimestamp(start_time).strftime("%A, %B %d, %Y %I:%M:%S")
    file = open("logs\\log_" + str(name_time[:8]) + ".txt","w")  # makeshift log -> needs to be improved
    cf.write_log(file, parameters, name_time, start_time)   # writes the different parameters into the log

    # This loop takes the pedictions at every epoch in the form of the five coins
    # with the highest prediction and plots the return at every timestep of
    # an inicial investment of "amount". Finally, it also stores these returns in the log.
    for i in range(len(predictions.predhis)):
        coins_historical = predictions.predhis[i] # Get the predictions at every epoch
        amount_historical, final_amount = cf.investment(coins_historical, df, parameters, percentages)
        cf.plot_investment(amount_historical, df, i, final_amount, parameters)
        cf.print_investment(coins_historical, amount_historical, i)
        file.write("\nReturn amount for epoch " + str(i + 1) + " is " + str(final_amount))

    file.close()

    #plt.show() # Show the plots computed in the previous loop

    cf.plot_loss(history) # we plot loss and validation loss
