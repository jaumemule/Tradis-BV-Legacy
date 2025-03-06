import uuid
import os
from ruamel.yaml import YAML
import datetime
import pandas as pd
from sqlalchemy import create_engine


# Import the config file
yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.boolean_representation = ['False', 'True']
with open( os.path.join("config.yml"), 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

database_path = cfg["other"]["database"]
database_name = "runs_v1"
engine_runs = create_engine(str(database_path) + database_name)


class Insert(object):
    def __init__(self, model_uuid):
        self.id = model_uuid
        self.hyper_id = uuid.uuid4()

    def insert_main(self, training_time, model_name, train_files):
        df = pd.DataFrame([dict(
            id=self.id,
            time=datetime.datetime.now(),
            training_time=training_time,
            model_name=model_name,
            train_files=[a for a in train_files]
        )]).set_index('id')
        with engine_runs.connect() as conn:
            df.to_sql('runs', conn, if_exists='append')

    def insert_hypers(self, cfg):
        patience = cfg["net"]["patience"]
        min_delta = cfg["net"]["min_delta"]
        which_model = cfg["training"]["which_model"]
        seq_len = cfg["training"]["seq_len"]
        dense_units = cfg["net"]["dense_units"]
        lstm_units = cfg["net"]["lstm_units"]
        dropout = cfg["net"]["dropout"]
        batch_size = cfg["net"]["batch_size"]
        epochs = cfg["net"]["epochs"]
        learning_rate = cfg["net"]["learning_rate"]
        l_rate_decay = cfg["net"]["l_rate_decay"]
        volumes = cfg["training"]["volumes"]
        forecast_len = cfg["training"]["forecast_len"]
        interval = cfg["training"]["interval"]
        scale = cfg["training"]["scale"]

        df = pd.DataFrame([dict(
            hyper_id=self.hyper_id,
            run_id=self.id,
            time=datetime.datetime.now(),
            which_model=which_model,
            epochs=epochs,
            seq_len=seq_len,
            forecast_len=forecast_len,
            interval=interval,
            scale=scale,
            volumes=volumes,
            dense_units=dense_units,
            lstm_units=lstm_units,
            batch_size=batch_size,
            dropout=dropout,
            l_rate_decay=l_rate_decay,
            learning_rate=learning_rate,
            patience=patience,
            min_delta=min_delta
        )]).set_index('hyper_id')

        with engine_runs.connect() as conn:
            df.to_sql('hypers', conn, if_exists='append')

    def insert_test(self, files):
        self.test_id = uuid.uuid4()
        df = pd.DataFrame([dict(
            test_id=self.test_id,
            run_id=self.id,
            time=datetime.datetime.now(),
            test_files=[a for a in files]
        )]).set_index('test_id')
        with engine_runs.connect() as conn:
            df.to_sql('test', conn, if_exists='append')

    def insert_ind_test(self, testing_time, file):
        self.individual_id = uuid.uuid4()
        df = pd.DataFrame([dict(
            individual_id=self.individual_id,
            ind_test_id=self.test_id,
            time=datetime.datetime.now(),
            testing_time=testing_time,
            test_files=file
        )]).set_index('individual_id')
        with engine_runs.connect() as conn:
            df.to_sql('individual_test', conn, if_exists='append')

    def insert_investments(self, test_file, coins_historical, final_amount):
        df = pd.DataFrame([dict(
            investment_id=uuid.uuid4(),
            individual_id=self.individual_id,
            test_file=test_file,
            investment_1=[x for x in coins_historical[0]],
            investment_2=[x for x in coins_historical[1]],
            investment_3=[x for x in coins_historical[2]],
            investment_4=[x for x in coins_historical[3]],
            investment_5=[x for x in coins_historical[4]],
            final_amount=final_amount
        )]).set_index('investment_id')
        with engine_runs.connect() as conn:
            df.to_sql('investments', conn, if_exists='append')


hyper_database = "hyper_runs"
hyper_engine_runs = create_engine(str(database_path) + hyper_database)


class HyperInsert(object):
    def __init__(self):
        try:
            conn = hyper_engine_runs.connect()
            conn.close()
        except:
            raise ConnectionError("Can't connect to database. Exiting.")

    def insert_main(self, training_time, testing_time, model_name, train_files, test_files, partial_results,
                    final_result, amount):
        self.id = uuid.uuid4()
        self.hyper_id = uuid.uuid4()
        df = pd.DataFrame([dict(
            id=self.id,
            time=datetime.datetime.now(),
            training_time=training_time,
            testing_time=testing_time,
            model_name=model_name,
            train_files=[a for a in train_files],
            test_files=[a for a in test_files],
            partial_results=[a for a in partial_results],
            final_result=final_result,
            amount=amount
        )]).set_index('id')
        with hyper_engine_runs.connect() as conn:
            df.to_sql('runs', conn, if_exists='append')

    def insert_hypers(self, cfg):
        patience = cfg["net"]["patience"]
        min_delta = cfg["net"]["min_delta"]
        which_model = cfg["training"]["which_model"]
        seq_len = cfg["training"]["seq_len"]
        dense_units = cfg["net"]["dense_units"]
        lstm_units = cfg["net"]["lstm_units"]
        dropout = cfg["net"]["dropout"]
        batch_size = cfg["net"]["batch_size"]
        epochs = cfg["net"]["epochs"]
        learning_rate = cfg["net"]["learning_rate"]
        l_rate_decay = cfg["net"]["l_rate_decay"]
        volumes = cfg["training"]["volumes"]
        forecast_len = cfg["training"]["forecast_len"]
        interval = cfg["training"]["interval"]
        scale = cfg["training"]["scale"]
        kernel_size = cfg["net"]["kernel_size"]
        pooling_size = cfg["net"]["pooling_size"]
        l2 = cfg['net']['l2']
        l1 = cfg['net']['l1']
        max_norm = cfg['net']['max_norm']

        df = pd.DataFrame([dict(
            hyper_id=self.hyper_id,
            run_id=self.id,
            time=datetime.datetime.now(),
            which_model=which_model,
            epochs=epochs,
            seq_len=seq_len,
            forecast_len=forecast_len,
            interval=interval,
            scale=scale,
            volumes=volumes,
            dense_units=dense_units,
            inner_units=lstm_units,
            batch_size=batch_size,
            dropout=dropout,
            l_rate_decay=l_rate_decay,
            learning_rate=learning_rate,
            patience=patience,
            min_delta=min_delta,
            kernel_size=kernel_size,
            pooling_size=pooling_size,
            l1=l1,
            l2=l2,
            max_norm=max_norm
        )]).set_index('hyper_id')

        with hyper_engine_runs.connect() as conn:
            df.to_sql('hypers', conn, if_exists='append')
