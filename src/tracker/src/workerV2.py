from src.domain.CouldNotRetrieveTrackerDataException import CouldNotRetrieveTrackerDataException
from src.domain.Tracker import Tracker
from src.application.SlackClient import Slack
from src.application.environmentConfigurations import EnvironmentConfigurations
from src.infra.Database import Database
from src.infra.Queueing import Queueing
from src.infra.TrackerRepository import TrackerRepository
from src.infra.ApiClient import ApiClient
from datetime import datetime
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import gc
import traceback

class Worker:

    retryCounter: int

    def __init__(self, method):
        self.method = method

        # retry if we could not retrieve the minutely data
        self.retryCounter = 0

        # this load will be kept in memory for the worker
        self.configurations = EnvironmentConfigurations()
        self.database = Database(self.configurations)
        self.queueing = Queueing(self.configurations)
        self.trackerRepository = TrackerRepository(self.configurations, self.database)
        self.apiClient = ApiClient(self.configurations)
        self.slack = Slack(self.configurations.slackToken, self.configurations.environmentName)
        self.slack.send('Tracker started in ' + self.configurations.environmentName + ' under mode ' + self.method)

    def work(self):

        # if self.configurations.environmentName != 'production':
        #     return

        self.unlockCoinsCheck = False
        if datetime.now().minute in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
            self.unlockCoinsCheck = True

        if datetime.now().minute in range(0, 60):
            # retry if we could not retrieve the minutely data
            self.retryCounter = 0
            self.__fire('BTC')

    def __fire(self, basedCoin):

        try:
            process: Tracker = Tracker(
                self.configurations,
                self.trackerRepository,
                self.apiClient,
                self.queueing
            )

            self.database.connectToAppropiateCollection(
                basedCoin,
            )

            process.track(basedCoin, self.unlockCoinsCheck)

            del process  # remove the instance to clear memory dedicated
            gc.collect()  # tell the garbage collector to empty memory, not sure if brings value

        except Exception as e:

            traceback_str = ''.join(traceback.format_tb(e.__traceback__)) + ' // message: ' + str(e)

            error = ":bangbang: " + traceback_str

            self.slack.send(error)

            gc.collect()  # tell the garbage collector to empty memory, not sure if brings value

worker = Worker('sandbox')

once_per_minute = CronTrigger('*', '*', '*', '*', '*', '*', '*', '0')
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(worker.work, trigger=once_per_minute, args = [], max_instances=1000)
sleep(1000000) # the script will last around 4 years
