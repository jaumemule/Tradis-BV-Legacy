from sklearn.preprocessing import StandardScaler
import numpy as np

class DataNormalizer:

    @staticmethod
    def forReinforcementLearningAgent(data, scale=True):
        fd = data.transpose()
        #X_test = fd.pct_change().replace([np.inf, -np.inf], np.nan).ffill()
        #X_test.iloc[0] = X_test.iloc[1]  # TODO FIXME: this needs to be improved asap
        if scale:
            X_test = StandardScaler().fit_transform(fd)
            X_test = X_test.transpose()

        else:
            X_test = fd.transpose().values
        X_test = np.nan_to_num(X_test)
        X_test = np.expand_dims(X_test, axis=0)
        return X_test
