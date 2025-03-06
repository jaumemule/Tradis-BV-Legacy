class AccountRuntimeEntity:

    def __init__(self, account):
        self.balanceLookupResult = {}
        self.entityInformation = account
        self.accountName = account['accountName']

    def getName(self):
        return self.accountName

    def setBalance(self, balance):
        self.balanceLookupResult = balance
