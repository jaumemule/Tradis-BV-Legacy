from logs import Log
import datetime
import uuid
from data import Data
from database.insert import Insert
from ruamel.yaml import YAML
import random
import os
import numpy as np
import pandas as pd
from tensorflow import set_random_seed
from keras.models import load_model
from utils import plot_investment, print_investment


yaml = YAML(typ='safe')
yaml.default_low_style = False
yaml.preserve_quotes = True
yaml.boolean_representation = ['False', 'True']
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

log = Log()
start_time = datetime.datetime.now()
log.print("Start time:" + str(start_time))
log.print(cfg)

random.seed(1102)  # ensuring reproducibility
np.random.seed(1102)  # same
set_random_seed(1102)  # yes, python sucks

# we list the data files we have:
path = os.getcwd()
data_path = os.path.join(path, "data")
data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
which_test = cfg["training"]["which_test"]
train_files = [x for x in data_files if data_files.index(x) not in which_test]
test_files = [x for x in data_files if data_files.index(x) in which_test]
if len(test_files) == 0:
    raise FileExistsError('The test files you are looking for do not exist. Exiting.')
volumes = cfg["training"]["volumes"]
complete = cfg["training"]["complete_testing"]

if not os.path.exists("logs"):
    os.makedirs("logs")
if not os.path.exists("charts"):
    os.makedirs("charts")
if not os.path.exists("investments"):
    os.makedirs("investments")

time = start_time
files = data_files if complete else test_files
model_name = cfg["other"]["model_name"]
model = load_model(os.path.join("models", model_name))
model_type = model.get_layer(index=-1).get_config()['activation']
# Initiate database insertion class
# model_uuid = cfg["other"]["model_uuid"]
model_uuid = uuid.uuid4()  # FIXME: don't even know what's going on here
insert = Insert(model_uuid)
training_time = 1234  # float(cfg["other"]["training_time"])/60  # FIXME: not an integer
insert.insert_main(training_time, model_name, train_files)  # FIXME: not correct now (new data)
insert.insert_hypers(cfg)
insert.insert_test(test_files)

for i, file in enumerate(test_files):
    print("============\nStarting testing for file " + str(i + 1) + " of " + str(len(files)) +
          " (this is file: " + str(file) + ")\n============")

    print("Importing and handling data...")

    data = Data(cfg)
    # data.import_from_db(first_date, day_number)
    data.import_from_csv(data_path, file)
    coin_list = data.filter_coins()
    data.create_raw()

    # TODO: make subselection of indices easier (i.e., only prices, volumes, etc)

    X_test, y_test, y_test_dates = data.test(model_type)
    X_test = np.expand_dims(X_test, -1)

    print("Starting predictions...")

    predictions = model.predict(X_test)

    if model_type == 'sigmoid':
        predictions = pd.DataFrame(np.round(predictions, 2), columns=coin_list, index=y_test_dates)
        predictions.to_csv('investments/predictions_run ' + str(which_test[i]) + '.csv')
        mod_eval = model.evaluate(X_test, y_test)
        print(mod_eval)

    else:

        predicted_coins = pd.DataFrame([np.argsort(a)[:5] for a in predictions])
        for index, row in predicted_coins.iterrows():
            predicted_coins.iloc[index, :] = [coin_list[a] for a in row]

        predicted_coins.index = y_test_dates

        print("Beginning investment simulations:")

        # for _ in tqdm(range(coins_historical.shape[0])):
        amount_historical, amount = data.investment(predicted_coins)

        plot_investment(amount_historical, data.df, "run_" + str(which_test[i]) + ".png", amount, data.forecast_len)
        print_investment(predicted_coins, amount_historical, "run_" + str(which_test[i]) + ".csv")
        print("The total amount is " + str(amount))
        test_time = datetime.datetime.now() - time
        log.print("Testing time for run " + str(i + 1) + " is " + str(test_time))
        time = datetime.datetime.now()
        log.print("The total amount for run " + str(i + 1) + " is " + str(amount))

        # insert.insert_ind_test(test_time/pd.Timedelta('1 minute'), file)
        # insert.insert_investments(file, coins_historical, amount)

    # TODO: add to log and ddbb the time period of the predictions

log.close()
