from ruamel.yaml import YAML
import uuid
import random
import os
import time
import datetime
import numpy as np
from data import Data
from models import ModelWrapper
from utils import plot_loss
from sklearn.utils import shuffle

from keras.callbacks import LearningRateScheduler, EarlyStopping
from keras.models import load_model
from keras.utils import to_categorical


# Import the configuration file
yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.boolean_representation = ['False', 'True']
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# random.seed(1102)  # ensuring reproducibility
# np.random.seed(1102)  # same
# set_random_seed(1102)  # yes, python sucks

# Unpack settings from the config file
out_files = cfg["training"]["out_files"]
patience = cfg["net"]["patience"]
min_delta = cfg["net"]["min_delta"]
which_model = cfg["training"]["which_model"]
seq_len = cfg["training"]["seq_len"]
dense_units = cfg["net"]["dense_units"]
inner_units = cfg["net"]["inner_units"]
dropout = cfg["net"]["dropout"]
model_name = cfg["other"]["model_name"]
batch_size = cfg["net"]["batch_size"]
epochs = cfg["net"]["epochs"]
learning_rate = cfg["net"]["learning_rate"]
l_rate_decay = cfg["net"]["l_rate_decay"]
volumes = cfg["training"]["volumes"]

# We have n>=11 files of training data; in this part we pick out_files of them randomly and we
# train on them. We store which we haven't picked in the config because those are the ones
# that the tester will use.
path = os.getcwd()
data_path = os.path.join(path, "data")
data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
files_index = random.sample(range(len(data_files)), out_files)
train_files = [x for x in data_files if data_files.index(x) not in files_index]
test_files = [x for x in data_files if data_files.index(x) in files_index]
cfg["training"]["which_test"] = files_index

# This is for retraining the model within the loop, but starting a new one before the loop
new_model = True
init_time = datetime.datetime.now()
# Configure learning rate and early stopping for keras:
er = EarlyStopping(monitor='val_loss',
                   min_delta=min_delta,
                   patience=patience,
                   verbose=1,
                   mode='auto')

if l_rate_decay:
    lrate = LearningRateScheduler(lambda x: learning_rate / (1. + x), verbose=1)
else:
    lrate = LearningRateScheduler(lambda x: learning_rate / (1. + 0), verbose=1)


subtract_pixel_mean=False
num_classes=2

# Here we start the run that trains for every file:
for i, file in enumerate(train_files):

    print("============\nStarting training for file " + str(i + 1) + " of " + str(len(train_files)) +
          " (this is: " + str(file) + ")\n============")

    # Convert class vectors to binary class matrices.

    #y_test = to_categorical(y_test, num_classes)

    data = Data(file, cfg, data_path)
    data.filter_coins()

    # if not volumes:
    #    data.df = data.df.iloc[::2]

    x_train, y_train = data.class_train()
    x_train, y_train = shuffle(x_train, y_train)
    y_train = to_categorical(y_train, num_classes)
    # If subtract pixel mean is enabled
    if subtract_pixel_mean:
        x_train_mean = np.mean(x_train, axis=0)
        x_train -= x_train_mean
        # x_test -= x_train_mean

    print('x_train shape:', x_train.shape)
    print(x_train.shape[0], 'train samples')
    # print(x_test.shape[0], 'test samples')
    print('y_train shape:', y_train.shape)

    #data_test = Data(test_files[0], cfg, data_path)
    #data_test.filter_coins()
    #X_test, y_test = data_test.class_test()


    dims = [x_train.shape[2], seq_len, dense_units, inner_units]
    if new_model:
        model_wrap = ModelWrapper(dims, cfg)
        model = model_wrap.build_model_(x_train.shape[1:])
        model_name = time.strftime("%Y_%m_%d_%H_%M_") + str(which_model) + ".h5"
        cfg["other"]["model_name"] = model_name

    else:
        model = load_model(os.path.join(path, "models", model_name))

    history = model.fit(
        x_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=0.2,
        #validation_data=(X_test, y_test),
        callbacks=[lrate, er])

    model.save(os.path.join(path, "models", model_name))
    new_model = False
    plot_loss(history, i)
    break

training_time = datetime.datetime.now() - init_time
cfg["other"]["training_time"] = str(training_time)
model_uuid = uuid.uuid4()
cfg["other"]["model_uuid"] = str(model_uuid)
with open("config.yml", 'w+') as ymlfile:
    yaml.dump(cfg, ymlfile)
