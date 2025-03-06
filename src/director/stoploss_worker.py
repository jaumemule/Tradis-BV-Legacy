import redis
from rq import Worker, SimpleWorker, Queue, Connection
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src import stoplossProcess

configurations = EnvironmentConfigurations()

listen = ['stoploss']

conn = redis.from_url(configurations.redisConnection)

if __name__ == '__main__':

    with Connection(conn):
        w = SimpleWorker(map(Queue, listen))
        w.work()
