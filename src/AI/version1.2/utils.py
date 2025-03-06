import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
import seaborn as sns


def plot_investment(amount_historical, df, name, final_amount, forecast_len):

    # TODO: find a way to add numbers in the x ticks
    fig, ax1 = plt.subplots(facecolor='white', figsize=(10, 6))
    ax1.plot(amount_historical, color="orange", label="Investment evolution")
    ax2 = ax1.twinx()

    ax2.plot(1/df.loc["TUSD.p"].iloc[::forecast_len], label="BTC evolution")
    plt.title(name + "\n The final amount is " + str(final_amount))
    ax1.legend()
    ax2.legend(loc=3)
    ax1.set_xticklabels([])
    ax2.set_xticklabels([])
    fig.tight_layout()

    plt.savefig(os.path.join("charts", name))
    plt.close()


def plot_investment_2(coins_historical, amount_historical, df, name, final_amount, forecast_len, seq_len):

    # TODO: find a way to add numbers in the x ticks
    ntemp = coins_historical.iloc[:, :-1].values
    (values, counts) = np.unique(list(ntemp.reshape((1, ntemp.shape[0] * ntemp.shape[1]))), return_counts=True)
    temp = pd.DataFrame(data = {"values" : values, "counts" : counts})

    df_temp = df.loc[list(temp.sort_values("counts").iloc[-5:,1].values)]
    df_temp = df_temp.iloc[:, (seq_len+forecast_len)::forecast_len]
    fd = df_temp.transpose()
    fd = pd.DataFrame(RobustScaler().fit_transform(fd))
    fd.index = df_temp.columns
    fd.columns = df_temp.index
    fd["amount"] = amount_historical
    fig, ax1 = plt.subplots(facecolor='white', figsize=(10, 6))
    ax1.plot(amount_historical, color="orange", label="Investment evolution")
    ax2 = ax1.twinx()
    sns.lineplot(data=fd.iloc[:, fd.columns != 'amount'], linewidth=1, ax=ax2)

    n = 50
    [l.set_visible(False) for (i, l) in enumerate(ax2.xaxis.get_ticklabels()) if i % n != 0]
    fig.autofmt_xdate()
    fig.tight_layout()

    plt.savefig(os.path.join("charts", name))
    plt.close()


def print_investment(coins_historical, amount_historical, name):

    coins_historical["amount"] = amount_historical
    coins_historical.to_csv(os.path.join("investments", name))


def plot_loss(history, i):

    plt.close()
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.savefig(os.path.join("charts", "loss_2" + str(i+1) + ".png"))
