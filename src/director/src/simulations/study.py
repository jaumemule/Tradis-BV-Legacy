import traceback
import datetime
import optuna
from src.simulations.logger import init_logger
from src.simulations.param_space import ParamSpace
from src.simulate import Worker
import gc

class Optimizer:
    opt_train_file = ""
    opt_test_file = ""
    train_file = ""
    validation_file = ""
    w_file_name = ""
    train_env = None
    test_env = None
    study_name = "whales_downs_with_lock_over_2020_no_march"
    database = 'sqlite:///src/simulations/results_server_1/server_1.db'

    def __init__(self):

        # Configs
        self.logger = init_logger("default", show_debug=True)

        # Initialize stuff
        self.optuna_study = None
        self.initialize_optuna()

    def initialize_optuna(self):

        self.study_name = f"{self.study_name}"
        self.optuna_study = optuna.create_study(
            study_name=self.study_name, storage=self.database, load_if_exists=True
        )

        self.logger.debug("Initialized Optuna:")

        try:
            self.logger.debug(
                f"Best reward in ({len(self.optuna_study.trials)}) trials: {self.optuna_study.best_value}"
            )
        except ValueError:
            self.logger.debug("No trials have been finished yet.")

    def optimize(self, n_trials: int = 20):
        try:
            self.optuna_study.optimize(
                self._optimize_params, n_trials=n_trials, n_jobs=-1
            )
        except KeyboardInterrupt:
            pass
        except:
            self.logger.error(traceback.format_exc())

        self.logger.info(f"Finished trials: {len(self.optuna_study.trials)}")

        try:
            self.logger.info(f"Best trial: {self.optuna_study.best_trial.value}")
        except ValueError:
            self.logger.warning(
                f"There where no non-pruned trials. This model/agent combo probably sucks."
            )
            return

        self.logger.info("Params: ")

        for key, value in self.optuna_study.best_trial.params.items():
            self.logger.info(f"    {key}: {value}")

        return self.optuna_study.trials_dataframe()

    def _get_trial(self, trial_id):
        if trial_id:
            # we see trial id's, which are consecutive by study, but, when we search, we do
            # within one study, so we need to adapt the numeration
            # first trial id
            first_id = self.optuna_study.trials[000].trial_id
            trial_num = trial_id - first_id
            trial = self.optuna_study.trials[trial_num]
        else:
            trial = self.optuna_study.best_trial

        return trial

    def _optimize_params(self, trial):

        # Initialize parameter space
        param_space = ParamSpace(trial)
        parameters = param_space.get_parameters()
        self.logger.info(f"The parameter space is {parameters}.")

        # Do the work
        worker = Worker(
            "simulation",
            datetime.datetime(2020, 4, 1, 0, 50, 0),
            datetime.datetime(2021, 1, 30, 0, 50, 0),
            False,
            parameters['hours_lock'] * 60,
            -1000,
            1000,
            parameters['whale_down'],
            1000,
            parameters['whale_minutes_lookup'],
            1000,
            False,
            True,
            60,
            'procyon',
            False,
            False
        )

        reward = worker.fireFromStudy()

        trial.report(-1 * reward, step=1)

        if trial.should_prune():
            raise optuna.structs.TrialPruned()

        # do not do that in multi thread
        # try:
        #     os.system("python src/scripts/cleanup_database.py")
        # except Exception:
        #     pass

        # empty memory
        del worker
        gc.collect()

        return -1 * reward
