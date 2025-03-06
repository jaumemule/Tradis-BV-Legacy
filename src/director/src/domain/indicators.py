import pandas as pd
import numpy as np


def ema(series, periods, fillna=False):
    if fillna:
        return series.ewm(span=periods, min_periods=0).mean()
    return series.ewm(span=periods, min_periods=periods).mean()


def rsi(close, n=14, forecast_len=20, fillna=False):
    """Relative Strength Index (RSI)
    Compares the magnitude of recent gains and losses over a specified time
    period to measure speed and change of price movements of a security. It is
    primarily used to attempt to identify overbought or oversold conditions in
    the trading of an asset.
    https://www.investopedia.com/terms/r/rsi.asp
    Args:
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.
    Returns:
        pandas.Series: New feature generated.
    """
    delta = close.diff(forecast_len)
    delta = delta[forecast_len:]
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    roll_up1 = up.ewm(n).mean()
    roll_down1 = down.abs().ewm(n).mean()
    RS = roll_up1 / roll_down1
    RSI = 100.0 - (100.0 / (1.0 + RS))
    if fillna:
        RSI = RSI.replace([np.inf, -np.inf], np.nan).fillna(50)

    return pd.Series(RSI, name='rsi')


def atr(df, open_col, high_col, low_col, close_col, forecast_len=20, n=14):
    # Suppress stupid warnings:
    pd.options.mode.chained_assignment = None

    # TODO: check this:
    temp = df.copy(deep=True)
    temp['max'] = temp[[open_col, high_col, low_col, close_col]].max(axis=1)
    temp['min'] = temp[[open_col, high_col, low_col, close_col]].min(axis=1)
    temp['val1'] = temp['max'] - temp['min']
    temp['val2'] = abs(temp['max'] - temp[close_col].shift(forecast_len))
    temp['val3'] = abs(temp['min'] - temp[close_col].shift(forecast_len))
    temp['tr'] = temp[['val1', 'val2', 'val3']].max(axis=1)
    temp['atr'] = None
    for i in range(forecast_len):
        temp['atr'].iloc[i::forecast_len] = temp['tr'].iloc[i::forecast_len].ewm(ignore_na=False,
                                                                                 min_periods=0,
                                                                                 com=n,
                                                                                 adjust=True).mean()

    return temp['atr']
