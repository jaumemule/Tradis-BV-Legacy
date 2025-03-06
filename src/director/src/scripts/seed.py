import pymongo
import os

### MAKE A COPY OF STAGING FROM THE DESIRED COLLECTIONS ####
### WILL REMOVE ALL THE OTHER COLLECTIONS THAT ARE NOT LISTED IN THE EXCEPTIONS ####

excludeCollectionsToBeRemovedInLocal = ['USDT', 'BTC']
copyFromRemote = ['coins', 'strategies']

localMongoConnection = os.getenv('MONGO_CONNECTION')
if not localMongoConnection:
    localMongoConnection = 'mongodb://localhost:27017/'

localClient = pymongo.MongoClient(localMongoConnection)
localDb = localClient.aggregated

remoteMongoConnection = os.getenv('MONGO_CONNECTION')

### TODO work on security here ####
remoteClient = pymongo.MongoClient('xxxxx')
remoteDb = remoteClient.aggregated

### PROCEED ON LISTING COLLECTIONS AND DELETING THEM ####
d = dict((db, [collection for collection in localClient[db].collection_names()])
         for db in localClient.database_names())

collectionList = []

for collection in d['aggregated']:
    collectionList.append(collection)


for collection in collectionList:
    if collection in excludeCollectionsToBeRemovedInLocal:
        print('did not remove: ', collection)
        continue

    connection = localDb[collection]
    connection.drop()
    print('dropped: ', collection)


for collection in copyFromRemote:
    remoteCollection = remoteDb[collection]
    localCollection = localDb[collection]

    for doc in remoteCollection.find():
        localCollection.insert(doc)
        print('imported: ', collection)



# for collection in collectionList:
#     connection = localDb[collection]