from rq import Queue
from redis import Redis

class Queueing:
    readyToPredict = 'director_job_listener.predict'
    triggerStopLoss = 'stoploss_job_listener.trigger'

    directorQueue = 'director'
    stoplossQueue = 'stoploss'

    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations
        conn = Redis.from_url(environmentConfigurations.redisConnection)
        self.queue_pool = {
            'director' : Queue(self.directorQueue, connection=conn),
            'stoploss' : Queue(self.stoplossQueue, connection=conn),
            'default' : Queue(connection=conn)
        }

    def enqueueSimpleTask(self, destination: str, origin: str, args: list = None, queue = 'default'):
        arguments = []
        arguments.append(origin)

        for arg in args:
            arguments.append(arg)

        self.queue_pool[queue].enqueue(destination, arguments)

    def emptyQueue(self, queue = 'default'):
        self.queue_pool[queue].empty()
