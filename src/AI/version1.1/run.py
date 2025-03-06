import lstm
import functions
import time
import sys
import random
import matplotlib.pyplot as plt
import numpy as np
from tensorflow import set_random_seed

random.seed(1102) # ensuring reproducibility
np.random.seed(1102)
set_random_seed(1102) # yes, python sucks

    # parameters
    # these parameters need to be adjusted to optimize the model
seq_len = 30 # be aware: not sure if ths number can be safely changed
epochs  = int(sys.argv[1]) # input the epochs from command line (for testing)
dense_units = 256 # this number needs to be played with (last best = 256)
lstm_units = 64*4 # ídem (last best = 64)
dropout = 0.2 # also
learning_rate = 0.00005 # (last best = 0.00005)
batch_size = 30 # original was 512
# I need to experiment with regularizers

#Main Run Thread
if __name__=='__main__':

    global_start_time = time.time()

    print('> Loading data... ')

    df1 = functions.data_load("CoinData_.csv")
    df1 = functions.poloniex_coins(df1) # we restrict to poloniex coins

    df2 = functions.data_load("coindata2.csv")
    df2 = functions.poloniex_coins(df2)

    df3 = functions.data_load("coindata3.csv")
    df3 = functions.poloniex_coins(df3)


    df_temp = df1.merge(df2, left_index=True, right_index = True)
    df = df_temp.merge(df3, left_index=True, right_index = True)

    X_train, y_train, X_test, y_test, scaler = functions.data_prep(df, seq_len)

    print('> Data Loaded. Compiling...')

    dims = [X_train.shape[2], seq_len, dense_units, lstm_units]
    # model = lstm.build_model2(dims, dropout, learning_rate)
    model = lstm.build_model2(dims, dropout, learning_rate)

    model.fit(
        X_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=0.1)

    end_time = time.time()
    fit_time = end_time - global_start_time

    print('Training duration (s) : ', fit_time)
    print('Now predicting...')

    # predicting
    preds = model.predict(X_test)
    predictions, y = functions.arrange(preds, y_test, seq_len, df, scaler)
    print('Prediction done in ', time.time() - end_time)

    # model evaluation metrics
    coins, total_sum = functions.find_best(y, predictions, 8)
    print("The sub-total sum of squares is " + str(total_sum))

    amount = 100
    fee = 0.0014
    amount_1, amount_2, amount_3, final_amount, historical = functions.invest_multi(y, predictions, seq_len, amount, fee)
    print("The final amount after a " + str(amount) + " euros investment is "+ str(final_amount) + " euros.")
    print("The separate amounts are "+ str(amount_1) + ", " + str(amount_2) + " and " + str(amount_3))
    # plotting
    functions.plot_preds(predictions, y, coins)

    functions.plot_multi(historical)
