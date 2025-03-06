# This code is obsolete! Please check run.py for the updated version.

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

# random.seed(1102)  # ensuring reproducibility
# np.random.seed(1102)  # same
# set_random_seed(1102)  # yes, python sucks

# Unpack settings from the config file
out_files = cfg["training"]["out_files"]
patience = cfg["net"]["patience"]
min_delta = cfg["net"]["min_delta"]
which_model = cfg["training"]["which_model"]
model_name = cfg["other"]["model_name"]
batch_size = cfg["net"]["batch_size"]
epochs = cfg["net"]["epochs"]

# We have n>=11 files of training data; in this part we pick out_files of them randomly and we
# train on them. We store which we haven't picked in the config because those are the ones
# that the tester will use.
path = os.getcwd()
data_path = os.path.join(path, "data")
data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
files_index = random.sample(range(len(data_files)), out_files)
train_files = [x for x in data_files if data_files.index(x) not in files_index]
cfg["training"]["which_test"] = files_index


# This is for retraining the model within the loop, but starting a new one before the loop
new_model = True
init_time = datetime.datetime.now()

# Here we start the run that trains for every file:
for i, file in enumerate(train_files):

    print("============\nStarting training for file " + str(i+1) + " of " + str(len(train_files)) +
          " (this is: " + str(file) + ")\n============")

    data = Data(cfg)
    data.import_from_csv(data_path, file)
    data.filter_coins()

    # Check how many coins we have
    coins = [a.split('.')[0] for a in list(data.df.index)]
    coin_number = len(set(coins))

    X_train, y_train = data.train()
    # X_train, y_train = shuffle(X_train, y_train)  # commented because it takes up too much RAM
    # FIXME: implement more efficiently

    training_observations = X_train.shape[2]

    if new_model:
        model_wrap = ModelWrapper(training_observations, coin_number, cfg)
        model = model_wrap.build_model_()
        model_name = time.strftime("%Y_%m_%d_%H_%M_") + str(which_model) + ".h5"
        cfg["other"]["model_name"] = model_name

    else:
        model = load_model(os.path.join(path, "models", model_name))

    history = model.fit(
        X_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=0.2,
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
