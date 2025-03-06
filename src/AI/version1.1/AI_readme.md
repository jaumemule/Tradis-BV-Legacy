This is the readme to run the AI models. Right now this only runs on Mac/Linux, but with very minor changes it can also work on Windows.

# Runing the models

To run the models we need to install:

* Conda (https://www.anaconda.com/download/) with Python 3.6
* keras: conda install keras

Then open a terminal, go to the directory where you downloaded everything and type 

    > python continuous_run.py N

Where N is the number of epochs (explained later)

In the begining you might have some errors because of missing libraries, just type 

    > conda install the_missing_library 
    
to install what's missing.

The model in the current settings takes around 2 minutes per epoch on my laptop.

# Files needed

### Data

* coindata_new.csv
* coin_filter.csv

The first file is the data file, no need to do anything. 
The second is the name of the coins that will be used for training and prediction (caveat: if you add any name of a coin that it's not in the tracker (so, not in coindata_new.csv) this coin will be ignored.) Add or remove names without changing the overall layout of the file (including the "" on the first line).

### Models

* functions.py
* continuous_functions.py
* lstm.py
* continuous_run.py

The first 2 are helper functions and I don't think you need to worry about them by now. 
The third file (lstm.py) contanis the actual models; you will see that it contains 6 models: numbered models from 1 to 4 range from simplest to most complex. There is also the model_chinese (which I copied from a chinese paper, hence the name) which is something between the models 1 and 2. There is also the model 2_reg, but don't worry about this one for now. What I have found so far is that beyond the second model, more complexity is not adding more performace, so I am mainly using this one. The chinese model is also very interesting. To train different models go to the final file, continuous_run.py. This is the main run file and the one you will be playing with. 

# Parameters

The different parameters to play with are:

### Model:
* which_model 

Obviously, choosing a model is a rather important parameter; it can be set to: 1, 2, "2reg", 3, 4, "chinese" (the quotes are important).

### Training and prediction lengths: 

* seq_len      
* forecast_len 

These two are probably the ones that affect the outcomes the most: the first (seq_len) is the length in minutes of the sequence used on the model and the second (forecast_len) is the forecast length in minutes of the prediction: that is, if we set seq_len = 60 and forecast_len = 30, que model will chop all the training data in sequences of 60 minutes and learn to predict 30 minutes into the future of each sequence.

Here you have an awesome schematic that will definitely not help you understand:

_________________________ --------------- *

         seq_len          forecast_len    Prediction

As I said, these two numbers are very important and we need to find the best combination. There is a problem with seq_len, and it's that on my 8Gb RAM laptop the maximum seq_len that I can set is 240 minutes; at some point I'll do something (either amazon or change code) to lengthen this maximum number.

### Number of neurons:
* dense_units
* lstm_units

These two parameters control the number of neurons in the different layers of the models. The dense_units control the number of neurons in the fully connected layers and the lstm_units in the LSTM layers. If you can watch the tutorials I sent you you will understand what they are. They are pretty important parameters, although my experience in this model is that increasing them doesn't change the result too much.

### Model fitting parameters:

* dropout
* learning_rate
* batch_size
* interval

These three parameters control how the fitting algorithm (a variation of gradient descent) looks for the best model. The dropout is used to avoid overfitting and shuts down a percentage of neuros at each step in order to force the model to split the weights (so the information in the neurons) among different neurons. 
The learning rate is the single most important parameter when fitting a neural network. It's not easy to explain all that can go wrong by choosing a wrong learning_rate, so I'll explain in a skype.

Batch size is related to learning_rate and doesn't need to be changed (I think).

Interval is a parameter that chooses how much space (in minutes) there is between the start of two training sequences. The minimum is 1 (there is a new training instance at each minute, and so the overlap is complete). This is an important parameter to control overfitting and to control RAM usage. RAM usage goes roughly as 1/interval. It can be thus used to practice with longer sequence lengths. 

### Prediction length

* train_days ---> deprecated
* pred_days

The AI wil use all available data *minus* the pred_days for data for model construction and tuning. Then it will test it's performance by predicting the pred_days. Aftewrards, the investment functions will compare the predictions with the reality and will check how rich we would be it this were real life. 

### Investing parameters

* amount = 100
* fee = 0.0014 * 2
* p1 = 0.4
* p2 = 0.3
* p3 = 0.2
* p4 = 0.1
* p5 = 0.
               
The first two are selfexplanatory, the other five control how much money is invested in each predicted coin. For example, in the case where we would want to invest everything on the highest predicted coin, we would just set p1 = 1 and all the rest equal to 0.

### Epochs

Finally, in the command to run the models you will enter the number of epochs. An epoch is a complete iteration over all training data; the number of epochs controls, together with learning rate and batch size, how the model is actually fitted to the data. I added this parameter in the command line because it's the one I was modifying more often; now I have created a callback that predicts the outcome of the model *after each epoch*, so that it's easier to choose the fitting procedure. I usually set it to 10, sometimes going up to 15 o 20.

# Model output

The model outputs some info in the command line and all the predictions in plots and documents in the three directories charts, investments and logs. 

First, it creates a log with all data of the model and the amount of money made at each epoch. Second, in the chart folder, you will find a plot for every epoch. At the end of every epoch it plots the investment progression over the prediction days (pred_days) and it compares it with the evolution of BTC during the same period of time so that one can compare. Also, it creates a model loss and validation loss chart; I'll explain what that is when we talk about learning rate and epochs and so on. Finally, it creates a document with each 5 highest predicted coins at every prediction step (the crypto masters might be very interested in this document). Please keep in mind that the logs are stored forever, but the charts and investment files are overriten at each model run. 