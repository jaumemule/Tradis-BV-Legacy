import re
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from keras.callbacks import EarlyStopping


# loading data
def data_load(filename):


    df = pd.read_csv(filename, error_bad_lines=False, index_col=0,  encoding='latin-1', engine='python')

    # nan cleaning: we eliminate coins with more than 30 missing values.
    df = df[df.isnull().sum(axis=1) < 30]

    # convert to numeric
    for col in df:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # interpolate the rest of the missing data
    df = df.interpolate(axis = 1, limit = 30)

    # normalize data --> removed, normalizing later to avoid data leakage
    # df_norm = df.subtract(np.mean(df, axis = 1), axis = 0).divide(np.std(df, axis = 1), axis = "rows")

    return df

def data_load_partial(filename, cols=None):


    df = pd.read_csv(filename, usecols=range(cols), error_bad_lines=False, index_col=0,
                     encoding='latin-1', engine='python')

    # nan cleaning: we eliminate coins with more than 30 missing values.
    df = df[df.isnull().sum(axis=1) < 30]

    # convert to numeric
    for col in df:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # interpolate the rest of the missing data
    df = df.interpolate(axis = 1, limit = 30)

    # normalize data --> removed, normalizing later to avoid data leakage
    # df_norm = df.subtract(np.mean(df, axis = 1), axis = 0).divide(np.std(df, axis = 1), axis = "rows")

    return df

# in this function we filter to only poloniex coins
def poloniex_coins(df):
    poloniex_coins = pd.read_csv("poloniex_coins.csv", index_col = 0)
    pol_coins = list(poloniex_coins.index)
    df_pol = df[df.index.isin(pol_coins)]

    return df_pol

def filter_coins(df):
    filtered_coins = pd.read_csv("binance_markets_in_bnb.csv", index_col = 0)
    filtered_coins = list(filtered_coins.index)
    df_filtered = df[df.index.isin(filtered_coins)]

    return df_filtered

# indices

#rsi

def compute_one_rsi(df):

    ups = df[df > 0].mean(skipna=True, axis = 1)
    downs = df[df < 0].mean(skipna=True, axis = 1)
    rs = ups/(-1*downs)
    rs.fillna(0, inplace = True)
    rsi = rs/(1+rs)

    return rsi

def compute_rsi_old(df, length = 14, gap = 24):
    df_h = df[df.columns[::gap*60]].iloc[::2]
    after = df_h.iloc[:,1:]
    before = df_h.iloc[:,:-1]
    diffs = (after - before.values)/before.values

    rsi = pd.DataFrame(index = diffs.index)

    for index, column in enumerate(diffs.iloc[:,length:]):
        rsi[column] = pd.Series(compute_one_rsi(diffs.iloc[:,index:(index + length)]), index = rsi.index)

    rsi.index = [x.replace("p","rsi") for x in rsi.index]

    return rsi


def compute_rsi(df, n=7):
    deltas = np.diff(df)
    seed = deltas[:, :n + 1]
    up = np.apply_along_axis(lambda axis: axis[axis >= 0].sum() / n, 1, seed)
    down = np.apply_along_axis(lambda axis: - axis[axis < 0].sum() / n, 1, seed)
    rs = np.divide(up, down, out=np.zeros_like(up), where=down != 0)
    rsi = np.zeros_like(df)
    rsi[:, :n] = np.swapaxes(np.tile(1. - 1. / (1. + rs), (n, 1)), 1, 0)

    for i in range(n, df.shape[1]):
        delta = deltas[:, i - 1]  # cause the diff is 1 shorter
        upval = np.where(delta > 0, delta, 0)
        downval = np.where(delta <= 0, -delta, 0)

        up = (up * (n - 1) + upval) / n
        down = (down * (n - 1) + downval) / n

        rs = np.divide(up, down, out=np.zeros_like(up), where=down != 0)
        rsi[:, i] = 1. - 1. / (1. + rs)

    rsi = pd.DataFrame(rsi, index=df.index, columns=df.columns)
    rsi.index = [x.replace("p", "rsi") for x in rsi.index]

    return rsi


def compute_ema(df, period=7):
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    a = np.apply_along_axis(lambda axis: np.convolve(axis, weights, mode='full')[:len(axis)], 1, df)
    a[:, :period] = np.swapaxes(np.tile(a[:, period], (period, 1)), 0, 1)

    a = pd.DataFrame(a, index=df.index, columns=df.columns)
    a.index = [x.replace("p", "ema") for x in a.index]

    return a


def compute_macd(df, slow=26, fast=12, signal_period=9):
    """
    compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
    return value is emaslow, emafast, macd which are len(x) arrays
    """
    emaslow = compute_ema(df, slow)
    emafast = compute_ema(df, fast)

    signal = compute_ema(emafast - emaslow, signal_period)

    return emaslow, emafast, signal

def normalize_index(index_df):
    rsi_transpose = index_df.transpose()  # need to transpose because StandardScaler only works on rows
    rsi_scaler = StandardScaler().fit(rsi_transpose)  # define the scaler
    rsi_transpose_std = rsi_scaler.transform(rsi_transpose)  # rescale data
    rsi_normalized = rsi_transpose_std.transpose()  # retranspose back to original
    rsi_normalized = pd.DataFrame(data=rsi_normalized,  # values
                                  index=index_df.index,  # 1st column as index
                                  columns=index_df.columns)

    return rsi_normalized, rsi_scaler

# stoch

def compute_stoch(df, length = 14):
    prices_df = df.iloc[::2,:]

    stoch = pd.DataFrame(index = prices_df.index)
    day = 60*24

    for index, column in enumerate(prices_df.iloc[:,length*day::60]):
        interval= prices_df.iloc[:,index:(24*length + index)]
        current = interval.iloc[:,-1]
        low = interval.min(axis = 1)
        high = interval.max(axis = 1)
        st = (current - low)/(high-low)
        st.fillna(0, inplace = True)

        stoch[column] = st

    stoch.index = [x.replace("p","stoch") for x in stoch.index]

    return stoch

# preparing data to enter the model
def data_prep(df, seq_len):

    # boring data handling #

    # we need to split the whole dataset into train and test in order to scale:
    row = round(0.8 * df.shape[1])
    df_train = df.iloc[:, :row]
    df_test = df.iloc[:, row:]

    # now we scale

    fd_train = df_train.transpose() # need to transpose because StandardScaler only works on rows
    fd_test = df_test.transpose()
    scaler = StandardScaler().fit(fd_train) # define the scaler
    fd_train_std = scaler.transform(fd_train) # rescale data
    fd_test_std = scaler.transform(fd_test)

    df_train = fd_train_std.transpose() # retranspose back to original
    df_test = fd_test_std.transpose()

    # initialize array with training data as rows (the last 30 entries are not used as training data), the number of
    # elements in any trainig example as columns and the number of coins as the third dimension
    X_train = np.zeros((df_train.shape[1]- 2*seq_len, df_train.shape[0], seq_len))
    y_train = np.zeros((df_train.shape[1] - 2*seq_len, df_train.shape[0]))
    X_test = np.zeros((df_test.shape[1] - 2*seq_len, df_test.shape[0], seq_len))
    y_test = np.zeros((df_test.shape[1] - 2*seq_len, df_test.shape[0]))

    # fill the array X_train
    for index in range(df_train.shape[1] - 2 * seq_len):
        X_train[index,:,:] = df_train[:, index: index + seq_len]

    # fill the array X_test
    for index in range(df_test.shape[1] - 2 * seq_len):
        X_test[index,:,:] = df_test[:, index: index + seq_len]

    X_train = np.swapaxes(X_train, 1, 2) # posem les monedes en la tercera dimensió per comoditat
    X_test = np.swapaxes(X_test, 1, 2)

    # fill the array y_train
    for index in range(2 * seq_len, df_train.shape[1]):
        y_train[index - 2 * seq_len,:] = df_train[:, index]

    # fill the array y_test
    for index in range(2 * seq_len, df_test.shape[1]):
        y_test[index - 2 * seq_len,:] = df_test[:, index]

    return X_train, y_train, X_test, y_test, scaler

def data_prep_rand(df, seq_len):

    # boring data handling #

    # we need to split the whole dataset into train and test in order to scale:
    row = round(0.8 * df.shape[1])
    df_train = df.iloc[:, :row]
    df_test = df.iloc[:, row:]

    # now we scale

    fd_train = df_train.transpose() # need to transpose because StandardScaler only works on rows
    fd_test = df_test.transpose()
    scaler = StandardScaler().fit(fd_train) # define the scaler
    fd_train_std = scaler.transform(fd_train) # rescale data
    fd_test_std = scaler.transform(fd_test)

    df_train = fd_train_std.transpose() # retranspose back to original
    df_test = fd_test_std.transpose()

    # initialize array with training data as rows (the last 30 entries are not used as training data), the number of
    # elements in any trainig example as columns and the number of coins as the third dimension
    X_train = np.zeros((df_train.shape[1]- 2*seq_len, df_train.shape[0], seq_len))
    y_train = np.zeros((df_train.shape[1] - 2*seq_len, df_train.shape[0]))
    X_test = np.zeros((df_test.shape[1] - 2*seq_len, df_test.shape[0], seq_len))
    y_test = np.zeros((df_test.shape[1] - 2*seq_len, df_test.shape[0]))

    # fill the array X_train
    for index in range(df_train.shape[1] - 2 * seq_len):
        X_train[index,:,:] = df_train[:, index: index + seq_len]

    # fill the array X_test
    for index in range(df_test.shape[1] - 2 * seq_len):
        X_test[index,:,:] = df_test[:, index: index + seq_len]

    X_train = np.swapaxes(X_train, 1, 2) # posem les monedes en la tercera dimensió per comoditat
    X_test = np.swapaxes(X_test, 1, 2)

    # fill the array y_train
    for index in range(2 * seq_len, df_train.shape[1]):
        y_train[index - 2 * seq_len,:] = df_train[:, index]

    # fill the array y_test
    for index in range(2 * seq_len, df_test.shape[1]):
        y_test[index - 2 * seq_len,:] = df_test[:, index]

    concat_train = np.concatenate((X_train, y_train), axis = 1)
    concat_test = np.concatenate((X_test, y_test), axis = 1)
    shuffled_train = np.random.shuffle(concat_train)
    shuffled_test = np.random.shuffle(concat_test)
    X_train = shuffled_train[:,:-1,:]
    y_train = shuffled_train[:,-1,:]
    X_test = shuffled_test[:,:-1,:]
    y_test = shuffled_test[:,-1,:]

    return X_train, y_train, X_test, y_test, scaler

## the model building is at the end of this document ##

# need to clean a few objects and rescale the predictions and the target values
def arrange(preds, y_test, seq_len, df, scaler):
    preds = preds[:(preds.shape[0] - 2 * seq_len),:]
    preds = scaler.inverse_transform(preds)
    predictions = pd.DataFrame(preds, columns = df.index)
    y = y_test[2 * seq_len:, :]
    y = scaler.inverse_transform(y)
    y = pd.DataFrame(y, columns = df.index)

    return predictions, y


# find n better predicted coins (eval metric is minimum sum of squares)
def find_best(y, predictions, n):
    # compute the squared distance between preds and y
    dist = np.sum(np.square((y - predictions)/y))
    ordered_dist = dist.sort_values()
    coins = ordered_dist.index[:n]

    # let's define of the 20 best predicted coins as a total model evaluation metric:
    # the rationale is that we don't need to predict all coins more or less correctly,
    # but we'd rather predict a few very well
    total_sum = np.sum(dist[:20])

    return coins, total_sum

# plotting
def plot_preds(predictions, y, coins):
    lines = round(len(coins)/2)
    fig = plt.figure(facecolor = 'white', figsize=(14, 10))
    for i, coin in enumerate(coins):
        plt.subplot(lines * 100 + 2 * 10 + i + 1)
        plt.plot(y[[coin]], label = 'True Data')
        plt.plot(predictions[[coin]] , label = 'Prediction')
        plt.title('Prediccions de ' + coin)
        plt.tick_params(axis = 'x', which = 'both', bottom = 'off',
                        top = 'off', labelbottom = 'off')
    plt.show()


### model evaluation

def invest(y, predictions, seq_len, amount, fee):
    A = predictions.iloc[30:,:]
    B = predictions.iloc[:-30,:]
    A.index = B.index
    diffs = (B.rsub(A)).divide(A)
    maximums = diffs.idxmax(axis = 1)
    points = np.arange(0, len(maximums), seq_len)
    maximums = maximums[points]
    historical = [amount]
    coins = [None]
    for i, coin in enumerate(maximums, -1):
        increase = amount*((y[coin].iloc[(i + 1)*seq_len] - y[coin].iloc[i *seq_len])/y[coin].iloc[i*seq_len]-fee)
        amount += increase
        coins.append(coin)
        historical.append(amount)

    return amount, coins, historical

def plot_investment(coins, historical):
    historical_data = pd.DataFrame({"coins": coins, "amount": historical})

    fig = plt.figure(facecolor='white', figsize=(10, 6))
    plt.xticks(historical_data.index, historical_data["coins"], rotation='vertical')
    plt.plot(historical_data.index, historical_data[["amount"]])
    plt.title("Historical investment return")
    plt.show()


def invest_multi(y, predictions, seq_len, amount, fee):
    p1 = 0.5
    p2 = 0.3
    amount_1 = amount * p1
    amount_2 = amount * p2
    amount_3 = amount * (1 - p1 - p2)
    fee = 2 * fee # since we will be trading through BTC, so twice

    A = predictions.iloc[30:,:]
    B = predictions.iloc[:-30,:]
    A.index = B.index
    diffs = (B.rsub(A)).divide(A)
    points = np.arange(0, predictions.shape[0], seq_len)

    # first investment:
    maximums = diffs.idxmax(axis=1)
    maximums = maximums.iloc[points[:-1]]
    historical_1 = [amount_1]
    coins_1 = [None]

    for i, coin in enumerate(maximums, -1):
        increase = amount_1*((y[coin].iloc[(i+1)*seq_len] - y[coin].iloc[i*seq_len])/y[coin].iloc[i*seq_len] - fee)
        amount_1 += increase
        coins_1.append(coin)
        historical_1.append(amount_1)

    # second investment:

    # we set the previous maximums to a very negative number so we can find the second biggest predictions
    # if at some point I find an idxmax function with the n largest items i will change it
    for i in points[:-1]:
        diffs[list(maximums)[int(i/30)]].iloc[i] = -100

    maximums = diffs.idxmax(axis=1)
    maximums = maximums.iloc[points[:-1]]
    historical_2 = [amount_2]
    coins_2 = [None]

    for i, coin in enumerate(maximums, -1):
        increase = amount_2*((y[coin].iloc[(i+1)*seq_len] - y[coin].iloc[i*seq_len])/y[coin].iloc[i*seq_len] - fee)
        amount_2 += increase
        coins_2.append(coin)
        historical_2.append(amount_2)

    # third investment:

    for i in points[:-1]:
        diffs[list(maximums)[int(i/30)]].iloc[i] = -100

    maximums = diffs.idxmax(axis=1)
    maximums = maximums.iloc[points[:-1]]
    historical_3 = [amount_3]
    coins_3 = [None]

    for i, coin in enumerate(maximums, -1):
        increase = amount_3*((y[coin].iloc[(i+1)*seq_len] - y[coin].iloc[i*seq_len])/y[coin].iloc[i*seq_len] - fee)
        amount_3 += increase
        coins_3.append(coin)
        historical_3.append(amount_3)

    historical = pd.DataFrame({"Coins A": coins_1, "Historical A": historical_1,
                               "Coins B": coins_2, "Historical B": historical_2,
                               "Coins C": coins_3, "Historical C": historical_3})

    return amount_1, amount_2, amount_3, amount_1 + amount_2 + amount_3, historical

def plot_multi(historical):

    cols = []
    for i in range(historical.shape[0]):
        cols.append(str(historical["Coins A"].iloc[i]) + "-" +
                    str(historical["Coins B"].iloc[i]) + "-" +
                    str(historical["Coins C"].iloc[i]))

    fig = plt.figure(facecolor='white', figsize=(10, 6))
    plt.xticks(historical.index, cols, rotation='vertical', fontsize=6)
    plt.plot(historical["Historical A"], label = "Investment A")
    plt.plot(historical["Historical B"], label = "Investment B")
    plt.plot(historical["Historical C"], label = "Investment C")
    plt.title("Historical investment return")
    plt.legend()
    plt.tight_layout()
    plt.show()

def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


# early stopping parameters

er = EarlyStopping(monitor='val_loss',
                   min_delta=0.002,
                   patience=2,
                   verbose=1,
                   mode='auto')