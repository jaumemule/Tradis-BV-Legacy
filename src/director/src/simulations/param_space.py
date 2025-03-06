class ParamSpace:

    def __init__(self, trial):
        self.trial = trial

    def get_parameters(self):
        return {
            "whale_down": self.trial.suggest_float("whale_down", 0, 10),
            "whale_minutes_lookup": self.trial.suggest_int("whale_minutes_lookup", 1, 15),
            "hours_lock": self.trial.suggest_int("hours_lock", 0, 12)
        }

    def get_trial_params(self):
        return self.trial.params
