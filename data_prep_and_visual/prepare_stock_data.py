import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
from yahoo_fin import stock_info
# from yahoo_fin.options import *
import stockstats
from stockstats import StockDataFrame as sdf
from pandas_datareader import data as pdr

import yfinance as yf

yf.pdr_override ()  # Override yfinance API in order to use Pandas DataReader

import numpy as np

end = datetime.date.today ()
end = datetime.datetime (end.year, end.month, end.day)  # to midnight of that day
start = (end - relativedelta (years=7))

# return list of Dow tickers
dow_tickers = pd.Series (stock_info.tickers_dow ())
sp_tickers = pd.Series (stock_info.tickers_sp500 ())
nasdaq_tickers = pd.Series (stock_info.tickers_nasdaq ())

# Indexes to run through and compared
'''
HUI:    Gold
XAU:    Silver
DXY:    USD
CL:     Oil
DJI:    Dow
SPY:    S&P 500 Index
NDAQ:   Nasdaq
'''

index_tickers = [ 'HUI', 'XAU', 'DXY', 'CL', 'DJI', 'SPY', 'NDAQ' ]
indicators = [ 'dma', 'volume_delta', 'close_12_ema', 'close_26_ema', 'macd', 'macd_9_ema', 'macds', 'macdh' ]


# Functions
# Returns the OCHLV for a stock over a 10 year period
def get_ticker_data(ticker):
    '''Takes a list of stock symbols and appends the open, close,
    high, low and trading day data from Yahoo Finance for that
    period.'''
    # return stock_info.get_data (ticker, start_date=start, end_date=end)
    return pdr.get_data_yahoo (ticker, start, end)


def get_indicator_data(symbols, symbol_data):
    '''Takes a list of symbols and the corresponding open, close,
    high, low and trading day data - then accesses the stockdataframe
    class to assign the MACD, EMA and other indicators for that time
    period.
        DMA, difference of 10 and 50 moving average - stock['dma']
        Volume delta against previous day - stock['volume_delta']
        MACD - stock['macd']
        MACD signal line - stock['macds']
        MACD histogram - stock['macdh']'''
    indicators = [ 'dma', 'volume_delta', 'close_12_ema', 'close_26_ema', 'macd', 'macd_9_ema', 'macds', 'macdh' ]
    indicator_data = pd.DataFrame ([ ])

    for i, j in enumerate (symbols):
        x_ind = sdf.retype (symbol_data [ symbol_data [ 'ticker' ] == j ])
        for m in indicators:
            x_ind [ x_ind [ m ] == x_ind [ m ] ]
        try:
            if i == 0:
                indicator_data = x_ind.copy ()
            else:
                indicator_data = indicator_data.append (pd.DataFrame (x_ind))
        except:
            continue
    return indicator_data


# Takes a list of ticker symbols and provides back a list of trade points
# date, open, close, high, low, volume
ticker_data = pd.DataFrame ([ ])
for ticker in dow_tickers:
    df = pd.DataFrame (get_ticker_data (ticker)).assign (ticker=ticker)
    ticker_data = ticker_data.append (df)

ticker_data.index.names = [ 'date' ]  # assigns a name to the index
ticker_data.reset_index (inplace=True)  # resets the index so that tradeday now becomes a column

# stock_ohc = pd.DataFrame ([ ])
stock_ohc = get_indicator_data (dow_tickers, ticker_data)

index_data = pd.DataFrame ([ ])
for index in index_tickers:
    df = pd.DataFrame (get_ticker_data (index)).assign (ticker=index)
    index_data = index_data.append (df)

index_data.index.names = [ 'date' ]  # assigns a name to the index

index_ohc = get_indicator_data (index_tickers, index_data)

# Now add back to the data_ticker df for one stock to the index information
stock_data = pd.concat ([ index_ohc, stock_ohc ], axis=0)


def get_movingavg(df, x):
    '''Takes in a df and numeric moving avg based on the number of days'''
    return df.loc [ :, 'close' ].rolling (x).mean ()


def get_prevclose(df, x):
    '''Takes in a df and variable to return the % change from the previous day'''
    # return (df [ x ] - df [ x ].shift (1)) / df [ x ].shift (1)
    return (df.loc [ :, x ] - df.loc [ :, x ].shift (1)) / df.loc [ :, x ].shift (1)

import copy

#Convert the df of stock data to a list of dataframes - one for each ticker

def get_indicators(df):
    '''Creates a list of dfs, one for each stock - then
    adds moving average, previous close and volume data
    Takes as input a dataframe of stock data'''
    key_names = df['ticker'].unique().tolist()
    df_history, df_recent = {}, {}
    for i in key_names:
        df_history [ i ] = df [ (df [ 'ticker' ] == i) ]
        df_history[i] [ "ma20" ] = get_movingavg (df_history[i], 20)
        df_history[i] [ "ma50" ] = get_movingavg (df_history[i], 50)
        df_history[i] [ "ma200" ] = get_movingavg (df_history[i], 200)
        df_history[ i ] [ "prev_close_ch" ] = get_prevclose (df_history[ i ], 'close')
        df_history[ i ] [ "prev_volume_ch" ] = get_prevclose (df_history[ i ], 'volume')
        df_recent[ i ] = df_history [ i ].iloc[-1:,:]
    return df_history, df_recent

stock_history, stock_recent = {}, {}
stock_history, stock_recent = get_indicators(stock_data)


#Appends to existing - could duplicate
try:
    if stock_data.index.max () == datetime.date.today ():
        f= open(r'/Users/jamesm/Desktop/Data_Science/stock_lstm/export_files/stock_recent.csv',"a")
        for df in stock_recent:
            stock_recent[df].to_csv(f, header=False)
        f.close()
except:
    print("Today's data has not yet been updated")

try:
    if stock_data.index.max () == datetime.date.today ():
        f= open(r'/Users/jamesm/Desktop/Data_Science/stock_lstm/export_files/stock_history.csv',"a")
        for df in stock_history:
            stock_history[df].to_csv(f, header=False)
        f.close()
except:
    print("Today's data has not yet been updated")


#Only needs to be run when there is a change to the headers - w will overwrite anyway.
headers = stock_history['AAPL'].columns
import csv
with open(r'/Users/jamesm/Desktop/Data_Science/stock_lstm/export_files/headers.csv',"w") as f:
    writer = csv.writer(f)
    writer.writerow(headers)

#Next step - set up the cron job on this to run daily, then build the vanilla model on it.