import lstm
import continuous_functions as cf
import class_functions
import class_lstm
import functions
import time
import sys
import random
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tensorflow import set_random_seed
from keras.callbacks import Callback, LearningRateScheduler

random.seed(1102) # ensuring reproducibility
np.random.seed(1102)
set_random_seed(1102) # yes, python sucks

epochs  = int(sys.argv[1]) # input the epochs from command line (for model testing purposes only)

# parameters
# these parameters need to be adjusted to optimize the model
seq_len = 180 # this is the amount of data (in minutes) used for the forecast
forecast_len = 20 # this is the forecast time in minutes
dense_units = 128 # this number needs to be played with (last best = 128)
lstm_units = 64 # ídem (last best = 64)
dropout = 0.5 # also (last best = 0.2)
learning_rate = 0.001 # (last best = 0.00005)
batch_size = 1280*2
# I need to experiment with regularizers

# other parameters

days = 18
number = days * 24 * 60
amount = 100
fee = 0.0014 * 2

class prediction_history(Callback):
    # This class is used to store the precictions (in form of predicted best coins)
    # for every epoch for testing purposes
    # more options and info on https://keras.io/callbacks/
    # I should add logs

    def __init__(self):
        self.predhis = []
    def on_epoch_end(self, epoch, logs={}):
        coins_historical = cf.coins(df, seq_len, forecast_len, number, scaler, model)
        self.predhis.append(coins_historical)

lrate = LearningRateScheduler(lambda x:  learning_rate / (1. + x), verbose = 1)

if __name__=='__main__':

    global_start_time = time.time()

    print('> Loading data... ')

    #df1 = functions.data_load("CoinData_.csv")
    #df1 = functions.poloniex_coins(df1) # we restrict to poloniex coins

    #df2 = functions.data_load("coindata2.csv")
    #df2 = functions.poloniex_coins(df2)

    df3 = functions.data_load("coindata_new.csv")
    df = functions.poloniex_coins(df3)

    #df_temp = df1.merge(df2, left_index=True, right_index = True)
    #df = df_temp.merge(df3, left_index=True, right_index = True)

    days = 3
    number = df.shape[1] - 60 * 24 * days # We predict only the last n days
    # (this line overrites the one in the parameters)

    X_train, y_train, scaler = class_functions.class_train(df, number, seq_len, forecast_len)

    predictions = prediction_history() # to have a prediction for every epoch

    dims = [X_train.shape[2], seq_len, dense_units, lstm_units]
    model = class_lstm.build_model2_reg(dims, dropout, learning_rate) # change the logs!
    history = model.fit(
        X_train,
        y_train,
        batch_size = batch_size,
        epochs = epochs,
        validation_split = 0.2,
        callbacks = [predictions, lrate])

    model.save('class_model.h5') # save the weights, just in case

    name_time = datetime.fromtimestamp(global_start_time).strftime("%A, %B %d, %Y %I:%M:%S")

    file = open("logs/class_log_" + str(name_time) + ".txt","w") # makeshift log -> needs to be improved

    file.write("Date and time: " + str(name_time))
    file.write("\n\nThe parameters for this model are:\n")
    file.write("\nModel used: " + "Model 2")
    file.write("\nSequence length: " + str(seq_len))
    file.write("\nForecast length: " + str(forecast_len))
    file.write("\nDense units: " + str(dense_units))
    file.write("\nLSTM units: " + str(lstm_units))
    file.write("\nDropout: " + str(dropout))
    file.write("\nLearning rate: " + str(learning_rate))
    file.write("\nBatch size: " + str(batch_size))
    file.write("\nPredicted length (in days): " + str(days))
    file.write("\nTrained length (in days): " + str(round(number/60/24,1)))
    delta = time.time() - global_start_time
    file.write("\nTraining duration (in minutes): " + str(round(delta/60,2)))

    accuracy = []
    for i in range(round((df.shape[1] - number - seq_len - forecast_len) / forecast_len)):
        X_test, y_test = class_functions.class_test(df, seq_len, number + i * forecast_len, forecast_len, scaler)
        X_test = np.expand_dims(X_test, axis = 0)
        y_test = np.expand_dims(y_test, axis = 0)
        scores = model.evaluate(X_test, y_test, verbose=0)
        accuracy.append(scores[1])
        # print(scores)
        # print("Accuracy: %.2f%%" % (scores[1]*100))
    mean_accuracy = round(np.mean(accuracy),3)
    print("Mean accuracy is: " + str(mean_accuracy) )
    #print(model.summary())
    file.write("\nMean accuracy is: " + str(mean_accuracy))
    file.close()
    cf.plot_loss(history) # we plot loss and validation loss
