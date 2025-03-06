from rq import Queue
from redis import Redis
conn = Redis.from_url('redis://localhost:6379')

print('queueing...')
q = Queue('director', connection=conn)
q.enqueue(
    'director_job_listener.predict',
    ['tracker', 'now']
)

### UTILS ###
# Retrieving jobs
# queued_job_ids = q.job_ids # Gets a list of job IDs from the queue
# queued_jobs = q.jobs # Gets a list of enqueued job instances
# job = q.fetch_job('my_id') # Returns job having ID "my_id"

# Emptying a queue, this will delete all jobs in this queue
q.empty()