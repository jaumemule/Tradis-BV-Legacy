import redis
from rq import Worker, SimpleWorker, Queue, Connection
from src.infra.environmentConfigurations import EnvironmentConfigurations
from src import Director

configurations = EnvironmentConfigurations()

listen = ['director']

conn = redis.from_url(configurations.redisConnection)

if __name__ == '__main__':

    with Connection(conn):
        w = SimpleWorker(map(Queue, listen))
        w.work()
