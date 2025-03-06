## this is meant to remove all the extra collections present in mongo that are not interesting
## for example, test collections or simulation collections

import pymongo
import os

exclude_from_removal = [
    'USDT',
    'accounts',
    'actionattempts',
    'coins',
    'max_users',
    'users',
    'strategies',
    'users',
    'transactions_ploutos_lead',
    'transactions_procyon_USDT_real_money',
    'pure_procyon_lead',
    'coinbasepro_EUR',
    'trades',
    'ai_observations_keras_coinbasepro',
    'ai_observations_ploutos',
    'ai_observations_procyon',
    'actions_keras_coinbasepro',
    'actions_ploutos',
    'actions_procyon',
    'trades',
    'simulations_aggregation',
]

localMongoConnection = os.getenv('MONGO_CONNECTION')
if not localMongoConnection:
    localMongoConnection = 'mongodb://localhost:27017/'

localClient = pymongo.MongoClient(localMongoConnection)
localDb = localClient.aggregated

### PROCEED ON LISTING COLLECTIONS AND DELETING THEM ####
d = dict((db, [collection for collection in localClient[db].collection_names()])
         for db in localClient.list_database_names())

collectionList = []

for collection in d['aggregated']:
    collectionList.append(collection)


for collection in collectionList:
    if collection in exclude_from_removal:
        print('did not remove: ', collection)
        continue

    connection = localDb[collection]
    connection.drop()
    print('dropped: ', collection)

connection = localDb['strategies']
connection.remove({'isSimulation': True})