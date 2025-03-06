from src.application.AccountRuntimeEntity import AccountRuntimeEntity

class AccountsContainer:

    def __init__(self):
        self.accountsList = {}

    def addAccount(self, accountName, entity = None):
        self.accountsList[accountName] = {
            'anonymousResultKey': {},
            'properties': entity
        }

    def getAccountProperties(self, accountName):
        if accountName in self.accountsList:
            return self.accountsList[accountName]['properties']
        return False

    def isAccountInTheList(self, accountName):
        if accountName in self.accountsList:
            return True
        return False

    def accountHasError(self, accountName): # check to not to break runtime
        return 'error' in self.accountsList[accountName]

    def updateAccount(self):
        pass

    def addResult(self, accountName, key, value):
        self.accountsList[accountName]['anonymousResultKey'][key] = value

    def getResult(self, accountName, key):

        if key in self.accountsList[accountName]['anonymousResultKey']:
            return self.accountsList[accountName]['anonymousResultKey'][key]

        return None

    def addError(self, accountName, value):
        self.accountsList[accountName]['error'] = value
        pass
