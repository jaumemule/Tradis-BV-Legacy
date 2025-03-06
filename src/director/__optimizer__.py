from src.simulations.study import Optimizer
import optuna

opt = Optimizer()
study = optuna.load_study(study_name=Optimizer.study_name, storage=Optimizer.database)
study.optimize(opt._optimize_params, n_trials=30)
