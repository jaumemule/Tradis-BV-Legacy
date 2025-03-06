import os

class EnvironmentConfigurations:

    currentlyRunningMethodology = 'sandbox' # default
    runMethodologySandbox = 'sandbox' # just a sandbox for the money
    runMethodologyProduction = 'real_money' # be careful! we are trading here :P

    ApiSecret = 'id'
    ApiId = 'secret'

    def __init__(self):

        environment = os.getenv('ENVIRONMENT')

        if environment == 'production' or environment == 'staging':
            self.redisConnection = os.getenv('REDIS_CONNECTION')
            self.mongoDbUrl = os.getenv('MONGO_CONNECTION')
            self.environmentName = environment
        elif environment == 'dev':
            self.redisConnection = 'redis://redis:6379'
            self.mongoDbUrl = 'mongodb://mongo:27017/'
            self.environmentName = environment
        else:
            self.redisConnection = 'redis://localhost:6379'
            self.mongoDbUrl = 'mongodb://localhost:27017/'
            self.environmentName = "dev_no_docker"

        if environment == 'production' or environment == 'staging':
            self.apiClientUrl = os.getenv('API_URL')
            self.internalWalletUrl = os.getenv('API_URL')
        else:
            self.apiClientUrl = 'http://api:3000/api/v1'
            self.internalWalletUrl = os.getenv('API_URL')

        self.slackToken = "xxxxxxxx"
