from src.domain.Tracker import Tracker
from src.application.environmentConfigurations import EnvironmentConfigurations
from src.infra.Database import Database
from src.infra.TrackerRepository import TrackerRepository
from src.infra.ApiClient import ApiClient
from src.domain.CouldNotRetrieveTrackerDataException import CouldNotRetrieveTrackerDataException
from src.infra.Queueing import Queueing

class Worker:

    # specify method while instantiating. so we can run different modes.
    # this can come by an env var

    def __init__(self, method):
        self.method = method

        # this load will be kept in memory for the worker
        configurations = EnvironmentConfigurations()
        self.configurations = configurations
        self.database = Database(configurations)
        self.trackerRepository = TrackerRepository(self.configurations, self.database)
        self.apiClient = ApiClient(self.configurations)
        self.queueing = Queueing(self.configurations)

        self.tracker: Tracker = Tracker(
            configurations,
            self.trackerRepository,
            self.apiClient,
            self.queueing
        )

    # we do not re-instantiate per iteration, just fire!
    def track(self):
        self.runOn('BTC')

    def runOn(self, basedCoin):

        self.database.connectToAppropiateCollection(
            basedCoin,
        )

        try:
            self.tracker.track(basedCoin, True)

        except CouldNotRetrieveTrackerDataException as e:
            error = ":bangbang: Could not retrieve the last minute of data from CryptoCompare"
            print(error)

worker = Worker('sandbox')
worker.track()
