# multichannel multi-step cnn for the power usage dataset
from math import sqrt
from numpy import split
from numpy import array
from pandas import read_csv
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot as plt
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from datetime import datetime, date

#The logic trains on the overlapping weeks but tests on mutually exclusive weeks. My issue is when updating the
#model with one day of data to make a 5 day prediction, on a daily, overlapped basis. This should be okay if the
#following conditions are met:

#the history dataset is capabale of having one day added to it
#history can then be expanded to the overlapped view so that we can run the 5 day prediction daily
#the model is ultimately trained on all data, overlapped.


def split_dataset(data, timesteps, train_pct):

	'''timesteps here should always be 1 - makes it more straightforward
	to send both test and train through the to_supervised function.'''

	leftover = data.shape[0]%timesteps 	# Reduce the data to a number divisible by 5
	weeks = data // timesteps			# determine total number of trading weeks

	data_sub = data[leftover:]			# Reduce the initial data to a number divisible by 5
	train_weeks = int(((data_sub.shape[0] * train_pct) // timesteps) * timesteps)
	train, test = data_sub[0:train_weeks], data_sub[train_weeks:]

	train = array(split(train, len(train) / timesteps))
	test = array(split(test, len(test) / timesteps))

	return train, test

train, test = split_dataset(dataset.values, 1, 0.8)

def create_history(data, timesteps):
	'''Returns a 3d image of the initial stock data'''
	return array(split(data, len(data) / timesteps))


history = create_history(dataset.values, 1)

#Do the initial data split, ensuring that each week overlaps. Training happens on the overlapping train set
#and then applied to the test set - rather than a weekly walk forward on test.
def split_data(data, timesteps, predsteps, train_pct):
	x_data, y_data = [], []
	in_start = 0
		# step over the entire history one time step at a time
	for _ in range (len (data)):
		# define the end of the input sequence
		in_end = in_start + timesteps
		out_end = in_end + predsteps
		# ensure there is enough to make a 5 day prediction
		if out_end <= len(data):
			x_data.append(data[in_start:in_end, :])
			y_data.append(data[in_end:out_end, 0])  # [:, 0] might have to factor
		in_start += 1
	x_data, y_data = np.array(x_data), np.array(y_data)
	train_weeks = int(x_data.shape[0] * train_pct)
	train_x, train_y, test_x, test_y = x_data[0:train_weeks], y_data[0:train_weeks], \
								   x_data[train_weeks:], y_data[train_weeks:]

	return train_x, test_x, train_y, test_y

train, train_y, test, test_y = split_data(dataset.values, 5, 7, 0.9)

#X = np.arange(0, 1000, 1)
#y = np.arange(1, 1001, 1)
#X = X.reshape(X.shape[0], 1)
#y = y.reshape(y.shape[0], 1)
#df = np.concatenate((X, y), axis=1)

# convert history into inputs and outputs
def to_supervised(train, n_input=14, n_out=7):
	# flatten data
	#data = train.reshape((train.shape[0]*train.shape[1], train.shape[2]))
	X, y = list(), list()
	in_start = 0
	# step over the entire history one time step at a time
	for _ in range(len(data)):
		# define the end of the input sequence
		in_end = in_start + n_input
		#out_end = in_end + n_out (in_end * timesteps) + n_out
		out_end = in_end + (in_end * timesteps) + n_out
		# ensure we have enough data for this instance
		if out_end <= len(data):
			X.append(data[in_start:in_end, :])
			y.append(data[in_end:out_end, 0])
		# move along one time step
		in_start += 1
	return array(X), array(y)


train_x, train_y = to_supervised(train, 14, 4)

'''
def timeseries_to_supervised(data, timesteps, predsteps):
    x_data, y_data = [ ], [ ]
    in_start = 0
    # step over the entire history one time step at a time
    for _ in range (len (data)):
        # define the end of the input sequence
        in_end = in_start + timesteps
        out_end = in_end + predsteps
        # ensure there is enough to make a 5 day prediction
        if out_end <= len (data):
            x_data.append (data [ in_start:in_end, : ])
            y_data.append (data [ in_end:out_end, 0 ]) #[:, 0] might have to factor
        # move along one time step
        in_start += 1
    x_data, y_data = np.array (x_data), np.array (y_data)
	#history = pd.concat(x_data, y_data)
	return x_data, y_data
	#return history

def split_data(X, y, train_pct):
    ##Takes in a dataset and returns an 80/20 split of train
    ##and test in the form of a numpy array

    split_size = int((int(X.shape[0]) * train_pct))
    x_train, x_dev = X[0:split_size, :, :], X[split_size:, :, :]
    y_train, y_dev = y[ 0:split_size, :], y [ split_size:, :]

    assert int(x_train.shape[0]) + int(x_dev.shape[0]) == int(X.shape[0])
    assert int(y_train.shape [ 0 ]) + int (y_dev.shape [ 0 ]) == int (y.shape [ 0 ])

    #return x_train, y_train, x_dev, y_dev
	return x_train, x_dev

'''


# evaluate one or more weekly forecasts against expected values
def evaluate_model(train, test, n_input):
	# fit model
	model = build_model(train, n_input)
	# history is a list of weekly data
	history = [x for x in train]
	# walk-forward validation over each week
	predictions, actuals = list(), list()
	for i in range(len(test)):
		# predict the week
		yhat_sequence = forecast(model, history, n_input)
		# store the predictions
		predictions.append(yhat_sequence)
		# get real observation and add to history for predicting the next week
		history.append(test[i, :])
		actuals.append(test[i, :])
	# evaluate predictions days for each week
	predictions = array(predictions)
	score, scores = evaluate_forecasts(test[:, :, 0], predictions)
	return score, scores, actuals, predictions

# summarize scores
def summarize_scores(name, score, scores):
	s_scores = ', '.join(['%.1f' % s for s in scores])
	print('%s: [%.3f] %s' % (name, score, s_scores))

# convert history into inputs and outputs
#def to_supervised(train, n_input, n_out=7):
	# flatten data
	#data = train.reshape((train.shape[0]*train.shape[1], train.shape[2]))
	#X, y = list(), list()
	#in_start = 0
	# step over the entire history one time step at a time
	#for _ in range(len(data)):
		# define the end of the input sequence
#		in_end = in_start + n_input#
#		out_end = in_end + n_out
#		# ensure we have enough data for this instance
#		if out_end <= len(data):
#			X.append(data[in_start:in_end, :])
#			y.append(data[in_end:out_end, 0])
#		# move along one time step
#		in_start += 1
#	return array(X), array(y)

# train the model
def build_model(train, n_input):
	# prepare data
	train_x, train_y = to_supervised(train, n_input)
	# define parameters
	verbose, epochs, batch_size = 1, 20, 32
	n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]
	# define model
	model = Sequential()
	model.add(Conv1D(96, 3, activation='relu', input_shape=(n_timesteps,n_features)))
	model.add(Conv1D(96, 3, activation='relu'))
	model.add(MaxPooling1D())
	model.add(Conv1D(64, 3, activation='relu'))
	model.add(MaxPooling1D())
	model.add(Flatten())
	model.add(Dense(100, activation='relu'))
	model.add(Dense(n_outputs))
	model.compile(loss='mse', optimizer='adam')
	# fit network
	model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size, verbose=verbose)
	return model

# make a forecast
def forecast(model, history, n_input):
	# flatten data
	data = array(history)
	data = data.reshape((data.shape[0]*data.shape[1], data.shape[2]))
	# retrieve last observations for input data
	input_x = data[-n_input:, :]
	# reshape into [1, n_input, n]
	input_x = input_x.reshape((1, input_x.shape[0], input_x.shape[1]))
	# forecast the next week
	yhat = model.predict(input_x, verbose=0)
	# yhat[0] is the first value of the sequence of 5 (or n_output)
	yhat = yhat[0]
	return yhat

# evaluate a single model
def evaluate_model(train, test, n_input):
	# fit model
	model = build_model(train, n_input)
	# history is a list of weekly data
	history = [x for x in train]
	# walk-forward validation over each week
	predictions, actuals = list(), list()
	for i in range(len(test)):
		# predict the week
		yhat_sequence = forecast(model, history, n_input)
		# store the predictions
		predictions.append(yhat_sequence)
		# get real observation and add to history for predicting the next week
		history.append(test[i, :])
		actuals.append(test[i, :])
	# evaluate predictions days for each week
	predictions = array(predictions)
	score, scores = evaluate_forecasts(test[:, :, 0], predictions)
	return score, scores, actuals, predictions


def process_data(ticker):

	headers = pd.read_csv (r'/home/ubuntu/stock_lstm/export_files/headers.csv')
	df = pd.read_csv (r'/home/ubuntu/stock_lstm/export_files/stock_history.csv', header=None, names=list(headers))
	df.index.name = 'date'

	df.reset_index (inplace=True)		#temporarily reset the index to get the week day for OHE
	df['date']= pd.to_datetime(df['date'])
	df [ 'day' ] = list (map (lambda x: datetime.weekday(x), df [ 'date' ])) #adds the numeric day for OHE
	df.set_index('date', inplace=True) #set the index back to the date field

	# use pd.concat to join the new columns with your original dataframe
	df = pd.concat([df,pd.get_dummies(df['day'],prefix='day',drop_first=True)],axis=1)

	df_close = df[df['ticker'] == ticker].sort_index(ascending=True)

	df_close = df_close.drop(['adj close', 'day', 'ticker',
						'volume_delta', 'prev_close_ch', 'prev_volume_ch', 'macds', 'macd', 'dma', 'macdh', 'ma200'],
					   axis=1)
	df_close = df_close.sort_index(ascending=True, axis=0)

	# Move the target variable to the end of the dataset so that it can be split into X and Y for Train and Test
	cols = list(df_close.columns.values)  # Make a list of all of the columns in the df
	cols.pop(cols.index('close'))  # Remove outcome from list
	df_close = df_close[['close'] + cols]  # Create new dataframe with columns in correct order

	df_close = df_close.dropna()

	fig, axes = plt.subplots (figsize=(16, 8))
		# Define the date format
	axes.xaxis.set_major_locator (mdates.MonthLocator (interval=6))  # to display ticks every 3 months
	axes.xaxis.set_major_formatter (mdates.DateFormatter ('%Y-%m'))  # to set how dates are displayed
	axes.set_title (ticker)
	axes.plot (df_close.index, df_close [ 'close' ], linewidth=3)
	plt.show ()

	return df_close

dataset = process_data('AAPL')

train, test = split_dataset(dataset.values, 5, 0.9)
#X, y = timeseries_to_supervised(dataset.values, 5, 5)
#train, test = split_data(X, y, 0.9)
# evaluate model and get scores
n_input = 14
score, scores, actuals, predictions = evaluate_model(train, test, n_input)
# summarize scores
summarize_scores('cnn', score, scores)
# plot scores
days = ['mon', 'tue', 'wed', 'thr', 'fri']
plt.plot(days, scores, marker='o', label='cnn')
plt.show()


#In plotting the actuals v predictions below, it is possible that the model is
#simply learning a persistance - that is, using the most recent value to make
#the prediction.
act = np.array(actuals)
day0_act = act[:, :, 0]
day0_act = day0_act.reshape(day0_act.shape[0]*day0_act.shape[1])

pred = np.array(predictions)
day0_pred = pred.reshape(pred.shape[0]*pred.shape[1])

for i in range(0, n_input):
	plt.plot (act[:, i, 0], color='blue')
	plt.plot (pred[:, i], color='orange')
	plt.title ("Actual v Prediction: Day " + str(i))
	plt.show ()

#Needs a bigger networks for example - more epochs + standardization - relu
#is not working at all.