from redis import Redis
from rq import Queue
from src.infra.environmentConfigurations import EnvironmentConfigurations

configurations = EnvironmentConfigurations()
conn = Redis.from_url(configurations.redisConnection)
q = Queue(connection=conn)

class Queueing:
    processAccounts = 'director_job_listener.processAccounts'

    directorQueue = 'director'

    def __init__(self, environmentConfigurations):
        self.environmentConfigurations = environmentConfigurations
        conn = Redis.from_url(environmentConfigurations.redisConnection)
        self.queue_pool = {
            'director' : Queue(self.directorQueue, connection=conn),
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
