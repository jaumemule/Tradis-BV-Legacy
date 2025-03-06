import os
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.externals import joblib
from sklearn.utils import shuffle
import matplotlib.pyplot as plt


def train(df, parameters):
    #### Unpack the parameters:
    number = parameters["number"]
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    interval = parameters["interval"]
    ####

    # Start the function
    df_train = df.iloc[:, :number]
    fd_train = df_train.transpose() # need to transpose because StandardScaler only works on rows
    scaler = StandardScaler().fit(fd_train) # define the scaler
    fd_train_std = scaler.transform(fd_train) # rescale data
    df_train = fd_train_std.transpose() # retranspose back to original

    # Initialization of training arrays:
    X_train = np.zeros((round((df_train.shape[1] - seq_len - forecast_len)/interval), df_train.shape[0], seq_len))
    y_train = np.zeros((round((df_train.shape[1] - seq_len - forecast_len)/interval), df_train.shape[0]))

    # Populating the arrays with the original data from df.
    for index in range(X_train.shape[0]):

        X_train[index,:,:] = df_train[:, index * interval: index * interval + seq_len]

    X_train = np.swapaxes(X_train, 1, 2) # set coins in the third dimension

    for index in range(round((seq_len + forecast_len)/interval), round(df_train.shape[1]/interval)):
        y_train[index - round((seq_len + forecast_len)/interval),:] = df_train[:, index*interval]

    # Save the scaler to be used in the director to avoid data leakage
    joblib.dump(scaler, "scaler.save")

    return X_train, y_train, scaler

def train_rand(df, parameters):  # deprecated!
    #### Unpack the parameters:
    number = parameters["number"]
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    interval = parameters["interval"]
    ####

    # Start the function
    df_train = df.iloc[:, :number]

    fd_train = df_train.transpose() # need to transpose because StandardScaler only works on rows
    fd_train = fd_train.pct_change().replace([np.inf, -np.inf], np.nan).bfill()
    scaler = StandardScaler().fit(fd_train) # define the scaler
    #fd_train_std = scaler.transform(fd_train) # rescale data
    df_train = fd_train.transpose() # retranspose back to original

    # Initialization of training arrays:
    X_train = np.zeros((round((df_train.shape[1] - seq_len - forecast_len)/interval), df_train.shape[0], seq_len))
    y_train = np.zeros((round((df_train.shape[1] - seq_len - forecast_len)/interval), df_train.shape[0]))

    # Populating the arrays with the original data from df.
    for index in range(X_train.shape[0]):

        X_train[index,:,:] = df_train[:, index * interval: index * interval + seq_len]

    X_train = np.swapaxes(X_train, 1, 2) # posem les monedes en la tercera dimensió per comoditat

    for index in range(round((seq_len + forecast_len)/interval), round(df_train.shape[1]/interval)-1):
        y_train[index - round((seq_len + forecast_len)/interval),:] = df_train[:, index*interval]

    y_train = np.expand_dims(y_train, axis = 2)
    y_train = np.swapaxes(y_train, 1, 2)
    idx = np.random.permutation(X_train.index) # shuffle training data to improve model learning
    X_train = X_train.reindex(idx)
    y_train = y_train.reindex(idx)

    # Save the scaler to be used in the director to avoid data leakage
    joblib.dump(scaler, "scaler.save")

    return X_train, y_train, scaler

# Now we start with the test data, 30 minutes at a time:
def test(df, seq_len, number, scaler):
    df_test = df.iloc[:, number:(number + seq_len)]
    fd_test = df_test.transpose()
    X_test = fd_test.pct_change().replace([np.inf, -np.inf], np.nan).ffill()
    X_test.iloc[0] = X_test.iloc[1]
    #X_test = scaler.transform(fd_test)

    return X_test

def coins(df, parameters, scaler, model): # currently not in use, see coins_new
    #### Unpack the parameters
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    number = parameters["number"]
    ####

    # The following function creates the test arrays from df and predicts the
    # highest raising coins for each forecast_len and stores them in coins_historical

    coins_historical = pd.DataFrame()
    for i in range(round((df.shape[1] - number - seq_len - forecast_len) / forecast_len)):
        X_test = test(df, seq_len, number + i * forecast_len, scaler)
        X_test = np.expand_dims(X_test, axis = 0)
        preds = model.predict(X_test)
        predictions = pd.DataFrame(preds.transpose(), index = df.index, columns = ["value"])
        investments = predictions.sort_values(by = "value", ascending = False)[:5]
        coins = list(investments.index)
        coins_historical[i] = coins

    return coins_historical

def coins_new(df, parameters, scaler, model, number_of_coins):
    #### Unpack the parameters
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    number = parameters["number"]
    ####

    # The following function creates the test arrays from df and predicts the
    # highest raising coins for each forecast_len and stores them in coins_historical
    coins_historical = pd.DataFrame()
    for i in range(round((df.shape[1] - number - seq_len - forecast_len) / forecast_len)):
        X_test = test(df, seq_len, number + i * forecast_len, scaler)
        X_test = np.expand_dims(X_test, axis = 0)
        preds = model.predict(X_test)
        predictions = pd.DataFrame(preds.transpose(), index = df.index, columns = ["value"])
        preds_new = predictions.iloc[:number_of_coins:2,:] # we are only considering predictions
                                                           # for prices, not volume or indices
        investments = preds_new.sort_values(by = "value", ascending = False)[:5]
        coins = list(investments.index)
        coins_historical[i] = coins

    return coins_historical

def coins_with_cluster(df, parameters, scaler, model, number_of_coins):
    #### Unpack the parameters
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    number = parameters["number"]
    clusters = pd.read_csv("clusters.csv", index_col=0)
    ####

    coins_historical = pd.DataFrame()
    for i in range(round((df.shape[1] - number - seq_len - forecast_len) / forecast_len)):
        X_test = test(df, seq_len, number + i * forecast_len, scaler)
        X_test = np.expand_dims(X_test, axis = 0)
        preds = model.predict(X_test)
        predictions = pd.DataFrame(preds.transpose(), index = df.index, columns = ["value"])
        preds_new = predictions.iloc[:number_of_coins:2,:]
        investments = preds_new.sort_values(by = "value", ascending = False)
        coins = list(investments.index)
        coins_historical[i] = coins

    return coins_historical

def gain(df, coin, parameters, i):
    # helper function to check amount gained for every coin invested


    #### Unpack the parameters and the percentages
    fee = parameters["fee"]
    number = parameters["number"]
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    ####
    if (df.loc[coin].iloc[number + seq_len + i * forecast_len])==0:
        gain = 0
    else:
        gain = ((df.loc[coin].iloc[number + seq_len + (i + 1) * forecast_len] -
             df.loc[coin].iloc[number + seq_len + i * forecast_len]) /
             df.loc[coin].iloc[number + seq_len + i * forecast_len] - fee)
    return gain

def investment(coins_historical, df, parameters, percentages):
    # another helper function to compute simulated rewards for investments

    #### Unpack the parameters and the percentages
    amount = parameters["amount"]
    fee = parameters["fee"]
    number = parameters["number"]
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    ####

    amount_historical = []
    for i in range(round((df.shape[1] - number - seq_len - forecast_len - max(0, forecast_len/seq_len - 1)) / forecast_len)):
        total_amount = []
        p_index = 0
        for key, value in percentages.items():
            coin = coins_historical.iloc[p_index, i]
            current_amount = amount * value
            current_amount += current_amount * gain(df, coin, parameters, i)
            total_amount.append(current_amount)
            p_index += 1

        amount = sum(total_amount)
        amount_historical.append(amount)

    return amount_historical, round(amount,2)

def investment_with_clusters(coins_historical, df, parameters, percentages):
    #### Unpack the parameters and the percentages
    amount = parameters["amount"]
    fee = parameters["fee"]
    number = parameters["number"]
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    ####

    clusters = pd.read_csv("clusters.csv", index_col=0)
    final_historical = pd.DataFrame()


    amount_historical = []
    for i in range(round((df.shape[1] - number - seq_len - forecast_len - max(0, forecast_len/seq_len - 1)) / forecast_len)):
        total_amount = []
        p_index = 0
        current_coins = coins_historical.iloc[:, i].values
        final_coins = []
        for key, value in percentages.items():

            coin = current_coins[p_index]

            try:
                cluster = clusters.loc[coin]

            except:
                cluster = 1000

            current_coins = [c for c in current_coins if clusters.loc[c].values != cluster.values]
            current_amount = amount * value
            current_amount += current_amount * gain(df, coin, parameters, i)
            total_amount.append(current_amount)
            final_coins.append(coin)
            p_index += 1

        amount = sum(total_amount)
        amount_historical.append(amount)
        final_historical[str(i)] = final_coins

    return amount_historical, round(amount,2), final_historical

def plot_investment(amount_historical, df, name, final_amount, parameters):
    #### Unpack the parameters
    number = parameters["number"]
    forecast_len = parameters["forecast_len"]
    unix = parameters["unix"]
    ####

    # I should find a way to add numbers in the x ticks

    fig, ax1 = plt.subplots(facecolor='white', figsize=(10, 6))
    ax1.plot(amount_historical, color = "orange", label = "Investment evolution")
    ax2 = ax1.twinx()

    ax2.plot(df.loc["XRP.p"].iloc[number::forecast_len], label = "XRP evolution")
    plt.title(name + "\n The final amount is " + str(final_amount))
    ax1.legend()
    ax2.legend(loc = 3)
    ax1.set_xticklabels([])
    ax2.set_xticklabels([])
    fig.tight_layout()
    #plt.draw()
    if unix:
        plt.savefig("charts/epoch_" + name + ".png")
    else:
        plt.savefig("charts\\epoch_" + name + ".png")

    plt.close()

def plot_investment_2(amount_historical, df, epoch, final_amount, number, forecast_len, predictions=None):
    # not working!

    lines = round(len(coins)/2)
    fig = plt.figure(facecolor='white', figsize=(14, 10))
    for i in range(epoch):
        plt.subplot(lines*100 + 2*10 + i + 1)
        plt.plot(y[[coin]], label='True Data')
        plt.plot(predictions[[coin]] , label='Prediction')
        plt.title('Prediccions de ' + coin)
        plt.tick_params(axis='x', which='both', bottom='off',
        top='off', labelbottom='off')
    plt.savefig("charts\\epoch_" + str(i + 1) + ".png")

def print_investment(coins_historical, amount_historical, i, parameters):
    unix = parameters["unix"]

    Coins = coins_historical.transpose()
    Coins["amount"] = amount_historical

    if unix:
        Coins.to_csv('investments/coins_epoch_' + str(i + 1) + '.csv')
    else:
        Coins.to_csv('investments\\coins_epoch_' + str(i + 1) + '.csv')

def plot_loss(history, parameters):

    unix = parameters["unix"]

    plt.close()
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    #plt.show()
    if unix:
        plt.savefig("charts/loss.png")
    else:
        plt.savefig("charts\\loss.png")

def write_log(file, parameters, name_time, start_time):
    #### Unpack the parameters:
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    dense_units = parameters["dense_units"]
    lstm_units = parameters["lstm_units"]
    dropout = parameters["dropout"]
    learning_rate = parameters["learning_rate"]
    batch_size = parameters["batch_size"]
    pred_days = parameters["pred_days"]
    number = parameters["number"]
    fee = parameters["fee"]
    amount = parameters["amount"]

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
    file.write("\nPredicted length (in days): " + str(pred_days))
    file.write("\nTrained length (in days): " + str(round(number/60/24,1)))
    delta = time.time() - start_time
    file.write("\nTraining duration (in minutes): " + str(round(delta/60,2)))
    file.write("\nFees: " + str(fee))
    file.write("\nInvestment: " + str(amount))
    file.write("\nThe returns for this investment are:\n")
