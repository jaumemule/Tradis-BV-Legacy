import pymongo
from bson.objectid import ObjectId

collectionsToCopy = [
    'transactions_keras_test_coinbasepro_EUR_real_money',
]


# collectionsToCopy = [
#     'transactions_02eb812252011a147d57af68f4b918eddde0a4ef2898e6788edf9ebd13bfdb80_keras_coinbasepro',
#     'transactions_0449a75a251ba69e3e980c750a1a9464493185ed7ceefebcd2efbc522395fdc1_procyon',
#     'transactions_25a37d348d3bd9443ecc05991d0fa57ce1a44d7bc827e65b42964c4bfcb98df9_procyon',
#     'transactions_27d6b2a7bbca1e90dc35d2332acace313f37e9a98b92f4416b867cb92a190f71_procyon',
#     'transactions_3e38b3f23bda7290d5e5e8aac436ef586e29e1c6f77e76dd83cd4baab5308b33_procyon',
#     'transactions_42181c7117161be4906d78f7c3eaf9ac9953bfc8e1f700819738ceff0499792f_procyon',
#     'transactions_4909c0174cc98d8f3b817179807e782324fffb45894ecb1f5e614e44e4832136_procyon',
#     'transactions_6ab17673ba3526706ad3aec914fbe87e669d2401e85ac994e796bc2a77bab5fb_keras_coinbasepro',
#     'transactions_72774151e2096349f9639ef89fdf654164570cd07515c2cb2220bf18c826cfd5_procyon',
#     'transactions_82981a0c390f8a0bc95c5a242249fd1cf13c0755614a12e6709d3cc5239242e6_procyon',
#     'transactions_8a66909a403b4f3b3250d33674e75eda42de3b486b5cd499f2afbae1af33881d_procyon',
#     'transactions_927d2700283233e209bebc41c304b254396fa89945636d2f9fdfd3fa37aeee0c_procyon',
#     'transactions_98efc22b48a0831c9f213f512a114263d68cc98ccb585e34d85b486aa9ae1b0d_procyon',
#     'transactions_LK2_binance_USDT_real_money',
#     'transactions_MC4564_binance_USDT_real_money',
#     'transactions_MK_coinbasepro_USDT_real_money',
#     'transactions_MP_binance_USDT_real_money',
#     'transactions_a2bf11b9a8e75d4e725ea28acab700638c7ad999be4fa11b6e5d3c04c092abb8_procyon',
#     'transactions_andreas_lassak_USDT_real_money',
#     'transactions_b1f962df9610e70f60ffdcbe15120bdf00c5fe833dfb3ddd59331f4fa44c3152_procyon',
#     'transactions_b2ce2b5c4dfb4d8559fe0ea1885330507c6e86d534692fc3e7f9ff8f48f78314_procyon',
#     'transactions_c01e611e4532ea7822067e866b35e8237db2232a4fcad4f0949d03bb0f193012_procyon',
#     'transactions_c341f0a26daf3f4815aa65e8d499f5edd824c6c77573bbfd673799b1d2fbcae7_keras_coinbasepro',
#     'transactions_coinbasepro_tradis_EUR_real_money',
#     'transactions_d169252398871abd46ad99a4283b0460cfbb0a0ce8a25923510131efc3f349f1_keras_coinbasepro',
#     'transactions_d67333e648753b2a1fc1fd311d641e7df466be9bc2c2e2a09f4c0b0581ed12f5_keras_coinbasepro',
#     'transactions_f668c0cbf44c95544a550c9a1ddb9eadd9ec53f7e54eff17def205197b86c513_keras_coinbasepro',
#     'transactions_fe08b55786742612742b871542562b2ee159d967e96ff27ca2c0a754341ee706_keras_coinbasepro',
#     'transactions_gilles_USDT_real_money',
#     'transactions_keras_USDT_real_money',
#     'transactions_lukas_kratochvil_USDT_real_money',
#     'transactions_procyon_USDT_real_money',
# ]


localMongoConnection = ''

client = pymongo.MongoClient(localMongoConnection, connect=False).aggregated

tradesCollection = client['trades']

tradesCollection.create_index("at")
tradesCollection.create_index("_account")

accountsCollection = client['accounts']

for collectionName in collectionsToCopy:

    collectionConnection = client[collectionName]

    for doc in collectionConnection.find():

        accountName = collectionName.split('transactions_')[1]

        account = accountsCollection.find_one({'accountName' : accountName})

        doc['_account'] = ObjectId(account['_id'])

        tradesCollection.save(doc)

    print('imported:' + collectionName)

print('account results migration has finished')