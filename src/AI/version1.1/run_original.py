import lstm
import time
import matplotlib.pyplot as plt
import sys

def plot_results(predicted_data, true_data):
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(111)
    ax.plot(true_data, label='True Data')
    plt.plot(predicted_data, label='Prediction')
    plt.legend()
    plt.show()

def plot_results_multiple(predicted_data, true_data, prediction_len):
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(111)
    ax.plot(true_data, label='True Data')
    #Pad the list of predictions to shift it in the graph to it's correct start
    for i, data in enumerate(predicted_data):
        padding = [None for p in range(i * prediction_len)]
        plt.plot(padding + data, label='Prediction')
        plt.legend()
        plt.title('Prediccions de ' + str(sys.argv[2]).upper())
    plt.show()

#Main Run Thread
if __name__=='__main__':
	global_start_time = time.time()
	epochs  = int(sys.argv[1]) # input the epochs from command line (for testing)
	seq_len = 30
	window_size = 30

	print('> Loading data... ')

	X_train, y_train, X_test, y_test = lstm.load_data(sys.argv[2], seq_len, True)

	print('> Data Loaded. Compiling...')


	model = lstm.build_model([1, 30, 100, 1])

	model.fit(
	    X_train,
	    y_train,
	    batch_size=512,
	    epochs=epochs,
	    validation_split=0.05)

	predictions = lstm.predict_sequences_multiple(model, X_test, window_size, seq_len)
	#predicted = lstm.predict_sequence_full(model, X_test, seq_len)
	#predicted = lstm.predict_point_by_point(model, X_test)

	print('Training duration (s) : ', time.time() - global_start_time)
    #plot_results(predicted, y_test)
	plot_results_multiple(predictions, y_test, 30)
