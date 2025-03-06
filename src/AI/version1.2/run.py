from ruamel.yaml import YAML
import uuid
import random
import os
import time
import datetime
from data import Data
from models import ModelWrapper
from utils import plot_loss
from sklearn.utils import shuffle

from callbacks import er, lrate, sigint_stop
from keras.models import load_model


# Import the configuration file
yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.boolean_representation = ['False', 'True']
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Unpack settings from the config file
n_train_files = cfg['training']['n_train_files']
n_test_files = cfg["training"]["n_test_files"]
which_model = cfg["training"]["which_model"]
model_type = cfg['training']['model_type']
model_name = cfg["other"]["model_name"]
batch_size = cfg["net"]["batch_size"]
epochs = cfg["net"]["epochs"]


# We have n>=29 files of training data; in this part we pick out_files of them randomly and we
# train on them. We store which we haven't picked in the config because those are the ones
# that the tester will use.
# TODO: this is a bit messy, put some order
path = os.getcwd()
data_path = os.path.join(path, "data", "tot")
data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
train_index = random.sample(range(len(data_files)), n_train_files)
all_files = list(range(len(data_files)))
test_index = random.sample([a for a in all_files if a not in train_index], n_test_files)
train_files = [x for x in data_files if data_files.index(x) in train_index]
test_files = [x for x in data_files if data_files.index(x) in test_index]
cfg["training"]["which_test"] = test_index


# This is for retraining the model within the loop, but starting a new one before the loop
new_model = True
init_time = datetime.datetime.now()

# Here we start the run that trains for every file:
for i, file in enumerate(train_files):
    print("============\nStarting training for file " + str(i + 1) + " of " + str(len(train_files)) +
          " (this is: " + str(file) + ")\n============")

    # This is for importing data directly from database, now it's too slow
    # TODO: implement efficiently
    # first_date = pd.to_datetime("2018-10-01 00:01:00", infer_datetime_format=True)
    # day_number = 3

    data = Data(cfg)
    data.import_from_csv(data_path, file)
    data.check_data()
    coin_names = data.filter_coins()
    data.create_raw()

    # Check how many coins we have
    coins = [a.split('.')[0] for a in list(data.df.index)]
    coin_number = len(set(coins))

    print('Training on ' + str(coin_number) + ' coins.')

    # How many training observations we have; to be passed to the model
    training_observations = int((data.df.shape[1] - data.seq_len - data.forecast_len)/data.interval)

    # If it's the first pass of the loop over files, create a new model; otherwise reuse the last one
    if new_model:
        model_wrap = ModelWrapper(training_observations, coin_number, cfg)
        model = model_wrap.build_model_(model_type)
        model_name = time.strftime("%Y_%m_%d_%H_%M_") + str(which_model) + ".h5"
        cfg["other"]["model_name"] = model_name

    else:
        model = load_model(os.path.join(path, "models", model_name))

    # Create X and y sets
    X_train, y_train = data.train(model_type)
    # X_train, y_train = shuffle(X_train, y_train)  # commented because it takes up too much RAM
    # FIXME: implement more efficiently

    history = model.fit(
        X_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=0.2,
        callbacks=[lrate, er, sigint_stop])

    model.save(os.path.join(path, "models", model_name))
    new_model = False
    sigint_stop.signal_received = False
    plot_loss(history, i)


training_time = datetime.datetime.now() - init_time
cfg["other"]["training_time"] = str(training_time)
model_uuid = uuid.uuid4()
cfg["other"]["model_uuid"] = str(model_uuid)
with open("config.yml", 'w+') as ymlfile:
    yaml.dump(cfg, ymlfile)
