from sqlalchemy import create_engine
from ruamel.yaml import YAML
import os.path

# Import the config file
yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.boolean_representation = ['False', 'True']
with open(os.path.join("..", "config.yml"), 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Connect to the database
database_path = cfg["other"]["database"]
database_name = "runs_v1"
engine_runs = create_engine(str(database_path) + database_name)

hyper_database = "hyper_runs"
hyper_engine_runs = create_engine(str(database_path) + hyper_database)

restart = False  # If set to true erases all tables; watch out!

# TODO: rethink structure
# TODO: add dates of datasets to database and logs


class DataBase(object):
    def __init__(self, engine_runs):
        self.conn_runs = engine_runs.connect()

    def setup_runs_table(self):
        self.conn_runs.execute("""
            create table if not exists runs
            (
                id uuid primary key,
                time date not null,
                training_time double precision,
                model_name varchar,
                train_files varchar[]
            );
        """)

    def setup_hypers_table(self):
        self.conn_runs.execute("""
            create table if not exists hypers
            (
                hyper_id uuid primary key,
                run_id uuid references runs(id),
                time date not null,
                forecast_len integer,
                interval integer,
                scale boolean,
                seq_len integer,
                volumes boolean,
                which_model varchar,
                epochs integer, 
                batch_size integer,
                dense_units integer,
                dropout numeric,
                l_rate_decay boolean,
                learning_rate double precision,
                lstm_units integer,
                patience integer,
                min_delta numeric
                );
        """)

    def setup_test_table(self):
        self.conn_runs.execute("""
            create table if not exists test
            (
                test_id uuid primary key,
                run_id uuid references runs(id),
                time date not null,
                test_files varchar[]
            );
        """)

    def setup_ind_test_table(self):
        self.conn_runs.execute("""
            create table if not exists individual_test
            (
                individual_id uuid primary key,
                ind_test_id uuid references test(test_id),
                time date not null,
                testing_time double precision,
                test_file integer,
                result numeric
            );
        """)

    def setup_investments_table(self):
        self.conn_runs.execute("""
            create table if not exists investments
            (
                investments_id uuid not null,
                ind_test_id uuid references individual_test(individual_id),
                time date not null,
                testing_time double precision,
                test_file integer,
                investment_1 varchar[],
                investment_2 varchar[],
                investment_3 varchar[],
                investment_4 varchar[],
                investment_5 varchar[],
                final_amount double precision[]
            );
        """)

    def drop_everything(self):
        # LOOKOUT! THIS WILL ERASE EVERYTHING!
        self.conn_runs.execute("""
        drop table if exists runs cascade;
        drop table if exists hypers cascade;
        drop table if exists test cascade;
        drop table if exists individual_test cascade;
        drop table if exists investments cascade
        """)


class HyperDataBase(object):
    def __init__(self, hyper_engine_runs):
        self.conn_runs = hyper_engine_runs.connect()

    def setup_runs_table(self):
        self.conn_runs.execute("""
            create table if not exists runs
            (
                id uuid primary key,
                time date not null,
                training_time double precision,
                testing_time double precision,
                model_name varchar,
                train_files varchar[],
                test_files varchar[],
                partial_results numeric[],
                final_result numeric, 
                amount numeric
            );
        """)

    def setup_hypers_table(self):
        self.conn_runs.execute("""
            create table if not exists hypers
            (
                hyper_id uuid primary key,
                run_id uuid references runs(id),
                time date not null,
                forecast_len integer,
                interval integer,
                scale boolean,
                seq_len integer,
                volumes boolean,
                which_model varchar,
                kernel_size integer,
                pooling_size integer,
                epochs integer, 
                batch_size integer,
                dense_units integer,
                dropout numeric,
                l1 numeric,
                l2 numeric,
                max_norm numeric,
                l_rate_decay boolean,
                learning_rate double precision,
                inner_units integer,
                patience integer,
                min_delta numeric
                );
        """)

    def drop_everything(self):
        # LOOKOUT! THIS WILL ERASE EVERYTHING!
        self.conn_runs.execute("""
        drop table if exists runs cascade;
        drop table if exists hypers cascade;
        drop table if exists test cascade;
        drop table if exists individual_test cascade;
        drop table if exists investments cascade
        """)


if __name__ == '__main__':

    # Set up the database
    db = DataBase(engine_runs)

    if restart:
        db.drop_everything()

    db.setup_runs_table()
    db.setup_hypers_table()
    db.setup_test_table()
    db.setup_ind_test_table()
    db.setup_investments_table()

    hdb = HyperDataBase(hyper_engine_runs)

    if restart:
        hdb.drop_everything()

    hdb.setup_runs_table()
    hdb.setup_hypers_table()

