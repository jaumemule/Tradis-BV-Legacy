import os
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

def class_train(df, parameters):

    #### Unpack the parameters:
    number = parameters["number"]
    seq_len = parameters["seq_len"]
    forecast_len = parameters["forecast_len"]
    interval = parameters["interval"]
    ####

    df_train = df.iloc[:, :number]
    fd_train = df_train.transpose() # need to transpose because StandardScaler only works on rows
    scaler = StandardScaler().fit(fd_train) # define the scaler
    fd_train_std = scaler.transform(fd_train) # rescale data
    df_train = fd_train_std.transpose() # retranspose back to original

    X_train = np.zeros((round((df_train.shape[1] - seq_len - forecast_len) / interval), df_train.shape[0], seq_len))
    y_train = np.zeros((round((df_train.shape[1] - seq_len - forecast_len) / interval), df_train.shape[0]))

    for index in range(X_train.shape[0]):
        X_train[index, :, :] = df_train[:, index * interval: index * interval + seq_len]

    X_train = np.swapaxes(X_train, 1, 2) # posem les monedes en la tercera dimensió per comoditat

    for index in range(round((seq_len + forecast_len) / interval), round(df_train.shape[1] / interval)):
        y_train[index - round((seq_len + forecast_len) / interval), :] = np.where(df_train[:, index*interval] > (df_train[:, index*interval - forecast_len]), 1, 0)

    return X_train, y_train, scaler

# Now we start with the test data, 30 minutes at a time:
def class_test(df, seq_len, number, forecast_len, scaler):

    df_test = df.iloc[:, number:(number + seq_len)]
    fd_test = df_test.transpose()
    X_test = scaler.transform(fd_test)
    y_test = np.where(df.iloc[:,number + seq_len + forecast_len] > df.iloc[:,number + seq_len], 1, 0)

    return X_test, y_test

def coins(df, seq_len, forecast_len, number, scaler, model):

    coins_historical = pd.DataFrame()
    for i in range(round((df.shape[1] - number - seq_len - forecast_len) / forecast_len)):
        X_test = class_test(df, seq_len, number + i * forecast_len, scaler)
        X_test = np.expand_dims(X_test, axis = 0)
        preds = model.predict(X_test)
        predictions = pd.DataFrame(preds.transpose(), index = df.index, columns = ["value"])
        investments = predictions.sort_values(by = "value", ascending = False)[:5]
        coins = list(investments.index)
        coins_historical[i] = coins

    return coins_historical

def gain(df, coin, number, forecast_len, fee, i):

    gain = ((df.loc[coin].iloc[number + (i + 2) * forecast_len] -
             df.loc[coin].iloc[number + (i + 1) * forecast_len]) /
             df.loc[coin].iloc[number + (i + 1) * forecast_len] - fee)
    return gain

def investment(amount, fee, coins_historical, df, number, seq_len, forecast_len):

    amount_historical = []
    for i in range(round((df.shape[1] - number - seq_len - forecast_len) / forecast_len)):

        amount1 = amount * 0.4
        amount2 = amount * 0.3
        amount3 = amount * 0.2
        amount4 = amount * 0.1
        amount5 = amount * 0

        coin1 = coins_historical.iloc[0, i]
        coin2 = coins_historical.iloc[1, i]
        coin3 = coins_historical.iloc[2, i]
        coin4 = coins_historical.iloc[3, i]
        coin5 = coins_historical.iloc[4, i]

        amount1 += amount1 * gain(df, coin1, number, forecast_len, fee, i)
        amount2 += amount2 * gain(df, coin2, number, forecast_len, fee, i)
        amount3 += amount3 * gain(df, coin3, number, forecast_len, fee, i)
        amount4 += amount4 * gain(df, coin4, number, forecast_len, fee, i)
        amount5 += amount5 * gain(df, coin5, number, forecast_len, fee, i)

        amount = amount1 + amount2 + amount3 + amount4 + amount5
        amount_historical.append(amount)

    return amount_historical, round(amount,2)

def plot_investment(amount_historical, df, epoch, final_amount, number, forecast_len):
    # I should find a way to add numbers in the x ticks

    fig, ax1 = plt.subplots(facecolor='white', figsize=(10, 6))
    ax1.plot(amount_historical, color = "orange", label = "Investment evolution")
    ax2 = ax1.twinx()
    ax2.plot(df.loc["BTC"].iloc[number::forecast_len], label = "BTC evolution")
    plt.title("Investment return for epoch " + str(epoch + 1) + "\n The final amount is " + str(final_amount))
    ax1.legend()
    ax2.legend(loc=3)
    ax1.set_xticklabels([])
    ax2.set_xticklabels([])
    fig.tight_layout()
    plt.draw()

def plot_investment_2(amount_historical, df, epoch, final_amount, number, forecast_len):
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
    plt.show()

def print_investment(coins_historical, amount_historical, i):
    Coins = coins_historical.transpose()
    Coins["amount"] = amount_historical
    Coins.to_csv('investments/coins_epoch_' + str(i + 1) + '.csv')

def plot_loss(history):
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()

def write_log(file):
    a = 2 # not implemented: need to pack the parameters in a dictionary
