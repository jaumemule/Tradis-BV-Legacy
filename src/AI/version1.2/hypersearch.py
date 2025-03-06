from ruamel.yaml import YAML
import uuid
import random
import os
import time
import datetime
import pickle
import warnings
from multiprocessing import Process, Queue
from slack import Slack
import numpy as np
import pandas as pd
from scipy.stats import trim_mean
from data import Data
from database.insert import HyperInsert
from models import ModelWrapper
from sklearn.utils import shuffle
from callbacks import er, lrate, sigint_stop
from keras.models import load_model
from keras.backend import clear_session
from hyperopt import fmin, tpe, hp, Trials
from hyperopt.pyll.base import scope
from keras.backend.tensorflow_backend import clear_session


debug = False


@scope.define
def two_to_the(x):
    return 2**int(x)


@scope.define
def ten_to_the_neg(x):
    return 10**-int(x)


@scope.define
def min_threshold(x, thresh, fallback):
    """Returns x or `fallback` if it doesn't meet the threshold. Note, if you want to turn a hyper "off" below,
    set it to "outside the threshold", rather than 0.
    """
    return x if (x and x > thresh) else fallback


@scope.define
def min_ten_neg(x, thresh, fallback):
    """Returns 10**-x, or `fallback` if it doesn't meet the threshold. Note, if you want to turn a hyper "off" below,
    set it to "outside the threshold", rather than 0.
    """
    x = 10**-x
    return x if (x and x > thresh) else fallback


@scope.define
def to_int(x):
    return int(x)


hyperspace = {}
hyperspace['model'] = hp.choice('model_type', [
    {
        'type': 'yang',
    },
    {
        'type': 'abe',
    },
    {
        'type': 'cnn',
    },

    ]),

hyperspace['dimensions'] = {
    #'dense_units': scope.to_int(hp.quniform('dense_units', 64, 256, 1)),
    #'inner_units': scope.to_int(hp.quniform('inner_units', 64, 256, 1)),
    'size': hp.uniform('size', 1, 5),
    'dropout': hp.uniform('dropout', .1, .6),
    'l2': scope.min_ten_neg(hp.uniform('l2', 2., 5.), 1e-5, 0.),
    'l1': scope.min_ten_neg(hp.uniform('l1', 2., 5.), 1e-5, 0.),
    'max_norm': hp.uniform('max_norm', 1, 3),
    'kernel_size': scope.to_int(hp.uniform('kernel_size', 2, 6)),
    'pooling_size': scope.to_int(hp.uniform('pooling_size', 1, 6)),
}

hyperspace['setup'] = {
    'seq_len': hp.choice('seq_len', [240, 300, 360, 480]),
    'forecast_len': scope.to_int(hp.quniform('forecast_len', 5, 30, 1)),
    'learning_rate': scope.ten_to_the_neg(hp.uniform('learning_rate', 2, 3)),
    'l_rate_decay': hp.choice('l_rate_decay', [True]),
}


def fill_cfg(hyperspace, cfg):
    # Unpack settings from the config file
    cfg["training"]["which_model"] = hyperspace['model'][0]['type']
    cfg["training"]["seq_len"] = hyperspace['setup']['seq_len']
    cfg["training"]["forecast_len"] = hyperspace['setup']['forecast_len']
    # cfg["net"]["dense_units"] = hyperspace['dimensions']['dense_units']
    # cfg["net"]["inner_units"] = hyperspace['dimensions']['inner_units']
    cfg["net"]["dropout"] = hyperspace['dimensions']['dropout']
    cfg['net']['l2'] = hyperspace['dimensions']['l2']
    cfg['net']['l1'] = hyperspace['dimensions']['l1']
    cfg['net']['max_norm'] = hyperspace['dimensions']['max_norm']
    cfg['net']['kernel_size'] = hyperspace['dimensions']['kernel_size']
    cfg['net']['pooling_size'] = hyperspace['dimensions']['pooling_size']
    cfg['net']['size'] = hyperspace['dimensions']['size']
    cfg["net"]["learning_rate"] = hyperspace['setup']['learning_rate']
    cfg["net"]["l_rate_decay"] = hyperspace['setup']['l_rate_decay']


def train_function(data, new_model, coin_number, cfg, path):
    # If it's the first pass of the loop over files, create a new model; otherwise reuse the last one
    training_observations = int((data.df.shape[1] - data.seq_len - data.forecast_len) / data.interval)
    which_model = cfg["training"]["which_model"]
    batch_size = cfg["net"]["batch_size"]
    epochs = cfg['net']['epochs']
    model_type = cfg['training']['model_type']
    if model_type == "sigmoid":
        warnings.warn("Look out, you are using classification models.")

    if new_model:
        model_wrap = ModelWrapper(training_observations, coin_number, cfg)
        model = model_wrap.build_model_()
        model_name = time.strftime("%Y_%m_%d_%H_%M_") + str(which_model) + ".h5"
        with open('model_name.txt', 'w+') as f:
            f.write(model_name)

    else:
        with open('model_name.txt', 'r') as f:
            model_name = f.read()
        model = load_model(os.path.join(path, "models", model_name))

    x_train, y_train = data.train(model_type)
    # X_train, y_train = shuffle(X_train, y_train)

    model.fit(
        x_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=0.2,
        callbacks=[lrate, er, sigint_stop])

    model.save(os.path.join(path, "models", model_name))


def test_function(q, data, cfg, coin_list, path, partial_rmse, rmse, amount, i):
    model_type = cfg['training']['model_type']
    with open('model_name.txt', 'r') as f:
        model_name = f.read()
    X_test, y_test, y_dates = data.test(model_type)
    model = load_model(os.path.join(path, "models", model_name))
    predictions = model.predict(X_test, verbose=1)

    if model_type == 'linear':
        rmse_list = trim_mean(np.subtract(predictions, y_test) ** 2, proportiontocut=.1, axis=0)
        temp_rmse = np.mean(rmse_list)
        partial_rmse.append(temp_rmse)
        rmse += temp_rmse
        predicted_coins = pd.DataFrame([np.argsort(a)[:5] for a in predictions])
        for index, row in predicted_coins.iterrows():
            predicted_coins.iloc[index, :] = [coin_list[a] for a in row]
        predicted_coins.index = y_dates
        _, temp_amount = data.investment(predicted_coins)
        amount += temp_amount
        q.put([partial_rmse, rmse, amount])

    else:
        predictions = pd.DataFrame(np.round(predictions, 2), columns=coin_list, index=y_dates)
        predictions.to_csv('predictions_run ' + str(i) + '.csv')
        mod_eval = model.evaluate(X_test, y_test)
        print(mod_eval)


# Here we start the run that trains for every file:
def main():
    clear_session()
    # Import the configuration file
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.boolean_representation = ['False', 'True']
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # Initialize the database and check that we can connect
    insert = HyperInsert()

    # We have n>=29 files of training data; in this part we pick out_files of them randomly and we
    # train on them. We store which we haven't picked in the config because those are the ones
    # that the tester will use.
    # TODO: this is a bit messy, put some order
    n_train_files = cfg['training']['n_train_files']
    n_test_files = cfg["training"]["n_test_files"]
    path = os.getcwd()
    data_path = os.path.join(path, "data", "tot")
    data_files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
    train_index = random.sample(range(len(data_files)), n_train_files)
    all_files = list(range(len(data_files)))
    test_index = random.sample([a for a in all_files if a not in train_index], n_test_files)
    train_files = [x for x in data_files if data_files.index(x) in train_index]
    test_files = [x for x in data_files if data_files.index(x) in test_index]
    cfg["training"]["which_test"] = test_index

    init_time = datetime.datetime.now()

    def run_fn(hyperspace):

        fill_cfg(hyperspace, cfg)
        print(hyperspace)

        new_model = True
        for i, file in enumerate(train_files):

            print("============\nStarting training for file " + str(i + 1) + " of " + str(len(train_files)) +
                  " (this is: " + str(file) + ")\n============")

            data = Data(cfg)
            data.import_from_csv(data_path, file)
            data.check_data()
            coin_list = data.filter_coins()
            data.create_raw()

            # Check how many coins we have and create a list to be used later on
            coins = [a.split('.')[0] for a in list(data.df.index)]
            coin_number = len(set(coins))
            print('Training on ' + str(coin_number) + ' coins.')

            # We are passing the training inside a subprocess in order to free the memory
            # captured by x_train and y_train and mitigate MemoryErrors
            # FIXME: do this more elegantly; can I pass a class inside a Process()?
            p = Process(target=train_function, args=(data, new_model, coin_number, cfg, path))
            p.start()
            p.join()  # this blocks until the process terminates
            new_model = False

        print("\nTraining finished, starting tests.\n")

        end_training = datetime.datetime.now()
        training_time = (end_training - init_time).total_seconds() / 60

        rmse = 0
        partial_rmse = []
        amount = 0
        for i, file in enumerate(test_files):
            data = Data(cfg)
            data.import_from_csv(data_path, file)
            _ = data.filter_coins()
            data.check_data()
            data.create_raw()

            q = Queue()
            p = Process(target=test_function, args=(q, data, cfg, coin_list, path, partial_rmse, rmse, amount, i))
            p.start()
            _list = q.get()
            partial_rmse = _list[0]
            rmse = _list[1]
            amount = _list[2]
            p.join()  # this blocks until the process terminates

        testing_time = (datetime.datetime.now() - end_training).total_seconds() / 60

        cfg["other"]["training_time"] = str(training_time)
        model_uuid = uuid.uuid4()
        cfg["other"]["model_uuid"] = str(model_uuid)
        with open('model_name.txt', 'r') as f:
            model_name = f.read()
        cfg['other']['model_name'] = model_name
        with open("config.yml", 'w+') as ymlfile:
            yaml.dump(cfg, ymlfile)

        insert.insert_main(training_time, testing_time, model_name, train_files, test_files,
                           partial_results=partial_rmse, final_result=rmse/len(test_files),
                           amount=amount/len(test_files))
        insert.insert_hypers(cfg)

        print("This run has resulted in a RMSE of " + str(rmse/len(test_files)))
        print("This run has resulted in an average amount of " + str(amount/len(test_files)))
        return rmse
        # Alternative would be return -amount

    max_evals = 100
    try:
        trialPickle = open('./trial.pickle', 'rb')
        trials = pickle.load(trialPickle)
        max_evals = len(trials.trials) + max_evals
    except:
        trials = Trials()

    best = fmin(run_fn, space=hyperspace, algo=tpe.suggest, max_evals=max_evals, trials=trials)

    if not debug:
        with open('./trial.pickle', 'wb') as f:
                pickle.dump(trials, f)


if __name__ == '__main__':
    warnings.warn('Look out, not connected to slack notifications upon Error.')
    main()

if False:
    try:
        main()
    except KeyboardInterrupt:
        pass
    except:
        slackToken = "xoxp-xxxxxxxxx"
        environmentName = 'production'
        slack = Slack(slackToken, environmentName)
        slack_message = "Training stopped in Barcelona (I have a lot of computers running this shit...)"
        slack.send(slack_message)
        raise